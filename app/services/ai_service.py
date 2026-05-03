import json
import logging
import random
import re
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.core.config import Settings, get_settings
from app.models.enums import ExerciseType
from app.models.material import Material
from app.services.correction_service import CorrectionResult, evaluate_answer as local_evaluate_answer

logger = logging.getLogger(__name__)

_SYSTEM_CORRECTION_JSON = """You grade English learner answers. Output ONLY compact JSON with keys:
correct (boolean), feedback (string in Portuguese), rewrite_student (string in English).

feedback: 3-5 short, friendly Portuguese sentences focused ONLY on "sua resposta".
Do NOT mention "gabarito", "resposta de referência", or compare against them explicitly.
If wrong/incomplete, make it didactic and practical in this order:
1) point out WHAT is wrong in sua resposta (specific words/parts, not vague);
2) explain WHY it is wrong in plain Portuguese with a tiny English-learning rule;
3) say HOW to fix it (pattern to use), ideally as a mini-contrast (wrong vs right choice), e.g. "How" pergunta modo/como algo acontece; "What" pede qual informação/identidade (data, nome, etc.)";
4) the LAST sentence must be that same kind of concrete rule/contrast tied to the mistake — NOT generic study advice.
FORBIDDEN as final content: empty motivational phrases, "preste atenção", "na próxima vez", "é importante para clareza", "estrutura das perguntas em inglês" without naming the specific linguistic reason, or anything that could replace a real explanation.
If correct: praise briefly and optionally suggest one refinement.
Use a supportive tone, direct and practical.

rewrite_student: ONE short English sentence that minimally fixes the student's own wording while keeping the SAME intent/topic they tried to express (repair grammar/vocabulary they used).
Hard max ~140 characters. If correct is true, use an empty string.
Do not paste the full reference answer verbatim unless the student's answer was empty or unusable; prefer a tight repair of their sentence.

Accept valid paraphrases when appropriate. Keep the whole JSON small to save tokens."""


@dataclass(frozen=True)
class GeneratedExercisePayload:
    question: str
    correct_answer: str
    explanation: str
    exercise_type: str


def _ai_configured(settings: Settings) -> bool:
    return bool(settings.ai_api_key.strip() and settings.ai_provider.strip())


_TRANSLATION_RULE = (
    "Translation rule (CRITICAL): for exercise_type \"translation\", every item MUST be Portuguese→English. "
    "The question must be written in Portuguese and must ask to translate a Portuguese sentence to English. "
    "correct_answer must be natural English only. Do NOT ask English→Portuguese unless the user message explicitly demands EN→PT "
    "(default in this app is always PT→EN). For mixed decks, any translation item must follow PT→EN."
)


def _truncate_for_prompt(text: str, max_len: int = 14_000) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n\n[… conteúdo truncado para limite do prompt …]"


_MOCK_PT_EN: list[tuple[str, str]] = [
    ("Eu preciso praticar inglês com mais frequência.", "I need to practice English more often."),
    ("Ela gosta de ler livros sobre história.", "She likes to read books about history."),
    ("Nós vamos viajar nas férias de verão.", "We are going to travel during the summer holidays."),
    ("Eu não entendi a explicação do professor.", "I didn't understand the teacher's explanation."),
    ("Eles trabalham em um escritório no centro da cidade.", "They work in an office downtown."),
    ("Minha mãe cozinha muito bem aos domingos.", "My mom cooks very well on Sundays."),
    ("Eu gostaria de melhorar minha pronúncia.", "I would like to improve my pronunciation."),
    ("O ônibus chegou cinco minutos atrasado.", "The bus arrived five minutes late."),
]

_MIX_TYPE_ROTATION: list[str] = [
    ExerciseType.TRANSLATION.value,
    ExerciseType.FILL_BLANK.value,
    ExerciseType.GRAMMAR.value,
    ExerciseType.TRANSLATION.value,
    ExerciseType.WRITING.value,
    ExerciseType.VOCABULARY.value,
    ExerciseType.MULTIPLE_CHOICE.value,
]


def _mock_deck_exercise_type(exercise_type: str, item_index: int) -> str:
    if exercise_type == "mixed":
        return _MIX_TYPE_ROTATION[item_index % len(_MIX_TYPE_ROTATION)]
    return exercise_type


def _normalize_for_compare(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" .,!?:;\"'`´“”‘’()[]{}")
    return s


def _unique_by_question(items: list[GeneratedExercisePayload]) -> list[GeneratedExercisePayload]:
    seen: set[str] = set()
    out: list[GeneratedExercisePayload] = []
    for item in items:
        key = _normalize_for_compare(item.question)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _mock_deck_from_material(
    material: Material, count: int, exercise_type: str = "mixed"
) -> list[GeneratedExercisePayload]:
    text = (material.content or "").strip()
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n+", text)
    segments = [re.sub(r"\s+", " ", p).strip() for p in parts if len(p.strip()) > 12]
    if not segments:
        segments = [re.sub(r"\s+", " ", text)[:200]] if text else ["(conteúdo vazio)"]
    rng = random.Random(f"{material.id}-{material.title}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    pt_en_pool = _MOCK_PT_EN[:]
    rng.shuffle(pt_en_pool)
    out: list[GeneratedExercisePayload] = []
    idx = 0
    while len(out) < count:
        ex_type = _mock_deck_exercise_type(exercise_type, len(out))
        if ex_type == ExerciseType.TRANSLATION.value:
            pt, en = pt_en_pool[len(out) % len(pt_en_pool)]
            out.append(
                GeneratedExercisePayload(
                    question=f"Traduza para o inglês: «{pt}»",
                    correct_answer=en,
                    explanation="Gerado localmente (mock). Tradução sempre de português para inglês.",
                    exercise_type=ExerciseType.TRANSLATION.value,
                )
            )
            continue
        seg = segments[idx % len(segments)]
        idx += 1
        seg_short = seg[:160]
        words = seg_short.split()
        ans = words[0] if words else "—"
        out.append(
            GeneratedExercisePayload(
                question=f'[{len(out) + 1}/{count}] ({ex_type}) Complete com a primeira palavra do trecho: "{seg_short}…" → _____',
                correct_answer=ans,
                explanation="Gerado localmente (mock) a partir do texto da aula.",
                exercise_type=ex_type,
            )
        )
    return out


def _mock_from_material(material: Material) -> GeneratedExercisePayload:
    snippet = (material.content or "").strip().replace("\n", " ")
    snippet = re.sub(r"\s+", " ", snippet)[:200]
    if not snippet:
        snippet = "(conteúdo vazio — adicione texto ao material)"
    blank_word = snippet.split()[0] if snippet.split() else "_____"
    return GeneratedExercisePayload(
        question=f'Complete a lacuna com a primeira palavra do trecho: "...{snippet[:120]}..." → A primeira palavra é: _____',
        correct_answer=blank_word,
        explanation="Exercício gerado localmente (modo mock). Configure AI_API_KEY e AI_PROVIDER para usar IA externa.",
        exercise_type=ExerciseType.FILL_BLANK.value,
    )


_SYSTEM_DECK_JSON = (
    "You are an English teacher. The user will send lesson notes (often from a PDF). "
    "Return ONLY valid JSON with a single key \"exercises\" whose value is an array of exactly N objects "
    "(N is given in the user message). Each object must have: question (string), correct_answer (string), "
    "explanation (string in Portuguese), exercise_type (one of: "
    f'{", ".join(e.value for e in ExerciseType)}). '
    "Exercises must reflect vocabulary, grammar, and ideas from the lesson. "
    "Do not repeat questions; each item must be distinct and cover different lesson points. "
    "When the user requests a fixed exercise type, use that type for all items. "
    "When the user requests 'mixed', vary types in a balanced way. "
    + _TRANSLATION_RULE
)


_SYSTEM_JSON = (
    "You are an English teacher. Return ONLY valid JSON with keys: "
    'question (string), correct_answer (string), explanation (string in Portuguese), '
    f'exercise_type (one of: {", ".join(e.value for e in ExerciseType)}). '
    "The question must be based on the study material provided. "
    + _TRANSLATION_RULE
)


def _parse_deck_json(raw: str) -> list[GeneratedExercisePayload]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    items = data["exercises"]
    if not isinstance(items, list):
        raise ValueError("exercises must be a list")
    out: list[GeneratedExercisePayload] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            GeneratedExercisePayload(
                question=str(item["question"]),
                correct_answer=str(item["correct_answer"]),
                explanation=str(item.get("explanation", "")),
                exercise_type=str(item.get("exercise_type", ExerciseType.FILL_BLANK.value)),
            )
        )
    return out


def _parse_json_payload(raw: str) -> GeneratedExercisePayload:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    return GeneratedExercisePayload(
        question=str(data["question"]),
        correct_answer=str(data["correct_answer"]),
        explanation=str(data.get("explanation", "")),
        exercise_type=str(data.get("exercise_type", ExerciseType.FILL_BLANK.value)),
    )


async def generate_exercise_from_material(material: Material, settings: Settings | None = None) -> GeneratedExercisePayload:
    settings = settings or get_settings()
    if not _ai_configured(settings):
        return _mock_from_material(material)

    provider = settings.ai_provider.lower().strip()
    user_block = (
        f"Title: {material.title}\n"
        f"Source type: {material.source_type}\n"
        f"Difficulty: {material.difficulty_level}\n"
        f"Content:\n{material.content}\n"
    )

    try:
        if provider == "openai":
            return await _call_openai(user_block, settings)
        if provider == "anthropic":
            return await _call_anthropic(user_block, settings)
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError, IndexError) as e:
        logger.warning("Falha na IA, usando mock local: %s", e)

    return _mock_from_material(material)


async def generate_exercise_deck_from_material(
    material: Material,
    count: int,
    settings: Settings | None = None,
    difficulty_level: str = "intermediate",
    exercise_type: str = "mixed",
) -> list[GeneratedExercisePayload]:
    settings = settings or get_settings()
    count = max(1, min(count, settings.max_deck_size))
    if not _ai_configured(settings):
        return _mock_deck_from_material(material, count, exercise_type=exercise_type)

    provider = settings.ai_provider.lower().strip()
    body_text = _truncate_for_prompt(material.content or "")
    user_block = (
        f"Generate exactly {count} exercises (N={count}).\n"
        f"Title: {material.title}\n"
        f"Source type: {material.source_type}\n"
        f"Difficulty for this deck: {difficulty_level}\n"
        f"Exercise type for this deck: {exercise_type}\n"
        "If exercise_type is 'mixed', diversify types across the deck.\n"
        "Avoid repeated questions or near-duplicates inside the same deck.\n"
        "Translation exercises must always be Portuguese→English (see system rules).\n"
        f"Lesson content:\n{body_text}\n"
    )

    try:
        if provider == "openai":
            got = await _call_openai_deck(user_block, count, settings)
        elif provider == "anthropic":
            got = await _call_anthropic_deck(user_block, count, settings)
        else:
            got = []
        got = _unique_by_question(got)
        if len(got) >= count:
            return got[:count]
        if got:
            rest = count - len(got)
            return got + _mock_deck_from_material(material, rest, exercise_type=exercise_type)[:rest]
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError, IndexError, TypeError) as e:
        logger.warning("Falha na IA (deck), usando mock local: %s", e)

    return _mock_deck_from_material(material, count, exercise_type=exercise_type)


async def _call_openai_deck(user_block: str, count: int, settings: Settings) -> list[GeneratedExercisePayload]:
    base = (settings.ai_base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}
    body = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_DECK_JSON},
            {"role": "user", "content": user_block},
        ],
        "temperature": 0.35,
        "max_tokens": 8192,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    content = data["choices"][0]["message"]["content"]
    parsed = _parse_deck_json(content)
    return parsed[:count] if len(parsed) > count else parsed


async def _call_anthropic_deck(user_block: str, count: int, settings: Settings) -> list[GeneratedExercisePayload]:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": settings.ai_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    model = settings.ai_model or "claude-3-5-haiku-20241022"
    body = {
        "model": model,
        "max_tokens": 8192,
        "system": _SYSTEM_DECK_JSON,
        "messages": [{"role": "user", "content": user_block}],
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    parsed = _parse_deck_json(text)
    return parsed[:count] if len(parsed) > count else parsed


async def _call_openai(user_block: str, settings: Settings) -> GeneratedExercisePayload:
    base = (settings.ai_base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}
    body = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_JSON},
            {"role": "user", "content": user_block},
        ],
        "temperature": 0.4,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    content = data["choices"][0]["message"]["content"]
    return _parse_json_payload(content)


async def _call_anthropic(user_block: str, settings: Settings) -> GeneratedExercisePayload:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": settings.ai_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    model = settings.ai_model or "claude-3-5-haiku-20241022"
    body = {
        "model": model,
        "max_tokens": 1024,
        "system": _SYSTEM_JSON,
        "messages": [{"role": "user", "content": user_block}],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return _parse_json_payload(text)


def _parse_correction_json(raw: str) -> CorrectionResult:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    ok = data["correct"]
    if isinstance(ok, str):
        ok = ok.strip().lower() in ("true", "1", "yes", "sim")
    else:
        ok = bool(ok)
    fb = str(data.get("feedback", "")).strip() or ("Aceitável." if ok else "Revise com base na pergunta.")
    hint_raw = data.get("rewrite_student")
    if hint_raw is None or hint_raw is False:
        hint = ""
    else:
        hint = str(hint_raw).strip()
    if hint:
        fb = f"{fb}\n\nSua frase em inglês (sugestão): «{hint[:450]}»"
    return CorrectionResult(ok, fb[:2500])


async def _call_openai_correction(user_block: str, settings: Settings) -> CorrectionResult:
    base = (settings.ai_base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}
    body = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_CORRECTION_JSON},
            {"role": "user", "content": user_block},
        ],
        "temperature": 0.15,
        "max_tokens": 620,
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    content = data["choices"][0]["message"]["content"]
    return _parse_correction_json(content)


async def _call_anthropic_correction(user_block: str, settings: Settings) -> CorrectionResult:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": settings.ai_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    model = settings.ai_model or "claude-3-5-haiku-20241022"
    body = {
        "model": model,
        "max_tokens": 620,
        "system": _SYSTEM_CORRECTION_JSON,
        "messages": [{"role": "user", "content": user_block}],
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return _parse_correction_json(text)


async def evaluate_submitted_answer_with_fallback(
    question: str,
    exercise_type: str,
    reference_answer: str,
    user_answer: str,
    exercise_explanation: str | None,
    settings: Settings | None = None,
) -> tuple[CorrectionResult, bool]:
    """Retorna (resultado, True se veio da API de IA)."""
    settings = settings or get_settings()
    # Diferenças apenas de maiúsculas/minúsculas/espaços/pontuação não contam como erro.
    if _normalize_for_compare(user_answer) == _normalize_for_compare(reference_answer):
        return (CorrectionResult(True, "Perfeito no conteúdo. Não consideramos diferença de maiúsculas/minúsculas aqui."), False)
    if not _ai_configured(settings) or not settings.use_ai_correction:
        return (local_evaluate_answer(user_answer, reference_answer, exercise_explanation), False)

    user_block = (
        f"type: {exercise_type}\n"
        f"Q: {question[:1200]}\n"
        f"Reference: {reference_answer[:800]}\n"
        f"Exercise hint: {(exercise_explanation or '')[:600]}\n"
        f"Student: {user_answer.strip()[:2000]}\n"
        "Important: the LAST sentence of feedback (Portuguese) must be a concrete linguistic contrast/rule "
        "tied to the student's mistake (e.g. how vs what), not generic study advice.\n"
    )
    provider = settings.ai_provider.lower().strip()
    try:
        if provider == "openai":
            result = await _call_openai_correction(user_block, settings)
        elif provider == "anthropic":
            result = await _call_anthropic_correction(user_block, settings)
        else:
            return (local_evaluate_answer(user_answer, reference_answer, exercise_explanation), False)
        return (result, True)
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError, TypeError, IndexError) as e:
        logger.warning("Correção IA falhou, usando regra local: %s", e)
        return (local_evaluate_answer(user_answer, reference_answer, exercise_explanation), False)

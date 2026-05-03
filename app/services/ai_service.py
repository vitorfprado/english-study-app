import json
import logging
import re
from dataclasses import dataclass

import httpx

from app.core.config import Settings, get_settings
from app.models.enums import ExerciseType
from app.models.material import Material

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedExercisePayload:
    question: str
    correct_answer: str
    explanation: str
    exercise_type: str


def _ai_configured(settings: Settings) -> bool:
    return bool(settings.ai_api_key.strip() and settings.ai_provider.strip())


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


_SYSTEM_JSON = (
    "You are an English teacher. Return ONLY valid JSON with keys: "
    'question (string), correct_answer (string), explanation (string in Portuguese), '
    f'exercise_type (one of: {", ".join(e.value for e in ExerciseType)}). '
    "The question must be based on the study material provided."
)


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

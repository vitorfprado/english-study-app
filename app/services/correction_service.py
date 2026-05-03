import re
from dataclasses import dataclass


def _normalize(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


@dataclass(frozen=True)
class CorrectionResult:
    is_correct: bool
    feedback: str


def evaluate_answer(user_answer: str, correct_answer: str, explanation: str | None = None) -> CorrectionResult:
    u = _normalize(user_answer)
    c = _normalize(correct_answer)
    if u == c:
        msg = "Correto."
        if explanation:
            msg += f" {explanation}"
        return CorrectionResult(True, msg)
    if c in u or u in c:
        return CorrectionResult(
            True,
            "Correto (equivalente próximo). "
            + (explanation or "Compare com a resposta esperada para refinar."),
        )
    msg = (
        "Sua resposta ainda tem problemas de estrutura e escolha de palavras para esse enunciado. "
        "Em inglês, mantenha uma ordem clara (sujeito + verbo + complemento) e use a forma verbal correta da expressão pedida."
    )
    if explanation:
        msg += f" Para corrigir, aplique esta regra: {explanation}"
    else:
        msg += " Para corrigir, reescreva em uma frase curta e natural, ajustando verbo, preposição e ordem das palavras."
    return CorrectionResult(False, msg)

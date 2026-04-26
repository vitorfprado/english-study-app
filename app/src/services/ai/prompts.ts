import { CardGenerationInput } from "@/types";

export function buildGenerateCardsPrompt(input: CardGenerationInput): string {
  return `Gere ${input.quantity} cards para estudo de ingles.
Retorne somente JSON valido (array) com os campos:
source_text_pt, expected_answer_en, alternative_answers, explanation_pt, tags, level.
Tema: ${input.theme}
Nivel: ${input.level}
Foco gramatical/vocabulario: ${input.grammarFocus}
As explicacoes devem estar em portugues do Brasil.`;
}

export function buildCorrectionPrompt(params: {
  sourceTextPt: string;
  expectedAnswerEn: string;
  alternativeAnswers: string[];
  userAnswer: string;
}): string {
  return `Avalie a traducao de portugues para ingles.
Retorne somente JSON valido com:
is_correct, score, correct_answer, user_answer_corrected, feedback_pt, grammar_tip_pt, alternative_answers.
Frase PT: ${params.sourceTextPt}
Resposta esperada: ${params.expectedAnswerEn}
Alternativas aceitas: ${params.alternativeAnswers.join(" | ")}
Resposta do usuario: ${params.userAnswer}`;
}

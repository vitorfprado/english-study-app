export type CardGenerationInput = {
  theme: string;
  level: string;
  quantity: number;
  grammarFocus: string;
};

export type GeneratedCard = {
  source_text_pt: string;
  expected_answer_en: string;
  alternative_answers: string[];
  explanation_pt: string;
  tags: string[];
  level: string;
};

export type AICorrectionResult = {
  is_correct: boolean;
  score: number;
  correct_answer: string;
  user_answer_corrected: string;
  feedback_pt: string;
  grammar_tip_pt: string;
  alternative_answers: string[];
};

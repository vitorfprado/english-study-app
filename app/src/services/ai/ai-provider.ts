import { AICorrectionResult, CardGenerationInput, GeneratedCard } from "@/types";

export interface AIProvider {
  generateCards(input: CardGenerationInput): Promise<GeneratedCard[]>;
  correctAnswer(params: {
    sourceTextPt: string;
    expectedAnswerEn: string;
    alternativeAnswers: string[];
    userAnswer: string;
  }): Promise<AICorrectionResult>;
}

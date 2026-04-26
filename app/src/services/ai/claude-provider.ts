import { z } from "zod";
import { AIProvider } from "./ai-provider";
import { buildCorrectionPrompt, buildGenerateCardsPrompt } from "./prompts";
import { AICorrectionResult, CardGenerationInput, GeneratedCard } from "@/types";

const generatedCardsSchema = z.array(
  z.object({
    source_text_pt: z.string(),
    expected_answer_en: z.string(),
    alternative_answers: z.array(z.string()).default([]),
    explanation_pt: z.string(),
    tags: z.array(z.string()).default([]),
    level: z.string()
  })
);

const correctionSchema = z.object({
  is_correct: z.boolean(),
  score: z.number().min(0).max(100),
  correct_answer: z.string(),
  user_answer_corrected: z.string(),
  feedback_pt: z.string(),
  grammar_tip_pt: z.string(),
  alternative_answers: z.array(z.string()).default([])
});

export class ClaudeProvider implements AIProvider {
  constructor(private readonly apiKey: string) {}

  async generateCards(input: CardGenerationInput): Promise<GeneratedCard[]> {
    const prompt = buildGenerateCardsPrompt(input);
    const data = await this.callClaude(prompt);
    return generatedCardsSchema.parse(data);
  }

  async correctAnswer(params: {
    sourceTextPt: string;
    expectedAnswerEn: string;
    alternativeAnswers: string[];
    userAnswer: string;
  }): Promise<AICorrectionResult> {
    const prompt = buildCorrectionPrompt(params);
    const data = await this.callClaude(prompt);
    return correctionSchema.parse(data);
  }

  private async callClaude(prompt: string): Promise<unknown> {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": this.apiKey,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 1500,
        messages: [{ role: "user", content: prompt }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API error: ${response.status} ${response.statusText}`);
    }

    const payload = (await response.json()) as {
      content?: Array<{ type: string; text?: string }>;
    };
    const text = payload.content?.find((item) => item.type === "text")?.text ?? "{}";

    try {
      return JSON.parse(text);
    } catch {
      throw new Error("Resposta da IA nao retornou JSON valido.");
    }
  }
}

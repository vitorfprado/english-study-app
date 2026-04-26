import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { getAIProvider } from "@/services/ai";
import { getOrCreateDefaultUser } from "@/lib/default-user";

const bodySchema = z.object({
  name: z.string().min(2),
  description: z.string().optional().default(""),
  theme: z.string().min(2),
  level: z.string().min(2),
  quantity: z.number().min(1).max(50),
  grammarFocus: z.string().min(2)
});

export async function POST(request: NextRequest) {
  try {
    const body = bodySchema.parse(await request.json());
    const user = await getOrCreateDefaultUser();
    const ai = getAIProvider();

    const generatedCards = await ai.generateCards({
      theme: body.theme,
      level: body.level,
      quantity: body.quantity,
      grammarFocus: body.grammarFocus
    });

    const deck = await prisma.deck.create({
      data: {
        name: body.name,
        description: body.description,
        theme: body.theme,
        level: body.level,
        userId: user.id,
        cards: {
          create: generatedCards.map((card) => ({
            sourceTextPt: card.source_text_pt,
            expectedAnswerEn: card.expected_answer_en,
            explanationPt: card.explanation_pt,
            alternativeAnswers: card.alternative_answers,
            tags: card.tags,
            level: card.level
          }))
        }
      }
    });

    return NextResponse.json({ deckId: deck.id }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Erro ao gerar deck.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

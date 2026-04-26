import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { getOrCreateDefaultUser } from "@/lib/default-user";
import { getAIProvider } from "@/services/ai";
import { jaccardSimilarity, normalizeEnglishText } from "@/lib/text-normalization";
import { getNextIntervalDays, getNextReviewDate, ReviewDifficulty } from "@/lib/scheduler";

const reviewSchema = z.object({
  cardId: z.string(),
  userAnswer: z.string().min(1),
  difficulty: z.enum(["wrong", "hard", "medium", "easy"])
});

export async function GET() {
  const card = await prisma.card.findFirst({
    where: { nextReviewAt: { lte: new Date() } },
    orderBy: { nextReviewAt: "asc" },
    select: { id: true, sourceTextPt: true }
  });

  return NextResponse.json({ card });
}

function localValidation(userAnswer: string, expected: string, alternatives: string[]) {
  const normalizedUser = normalizeEnglishText(userAnswer);
  const allExpected = [expected, ...alternatives].map(normalizeEnglishText);
  if (allExpected.includes(normalizedUser)) {
    return { isClearCorrect: true, isDoubtful: false, score: 100 };
  }

  const similarity = Math.max(...allExpected.map((candidate) => jaccardSimilarity(normalizedUser, candidate)));
  if (similarity < 0.55) return { isClearCorrect: false, isDoubtful: false, score: Math.round(similarity * 100) };

  return { isClearCorrect: false, isDoubtful: true, score: Math.round(similarity * 100) };
}

export async function POST(request: NextRequest) {
  try {
    const body = reviewSchema.parse(await request.json());
    const user = await getOrCreateDefaultUser();
    const card = await prisma.card.findUnique({ where: { id: body.cardId } });

    if (!card) {
      return NextResponse.json({ error: "Card nao encontrado." }, { status: 404 });
    }

    const alternatives = Array.isArray(card.alternativeAnswers) ? (card.alternativeAnswers as string[]) : [];
    const localResult = localValidation(body.userAnswer, card.expectedAnswerEn, alternatives);

    const feedback = localResult.isDoubtful
      ? await getAIProvider().correctAnswer({
          sourceTextPt: card.sourceTextPt,
          expectedAnswerEn: card.expectedAnswerEn,
          alternativeAnswers: alternatives,
          userAnswer: body.userAnswer
        })
      : {
          is_correct: localResult.isClearCorrect,
          score: localResult.score,
          correct_answer: card.expectedAnswerEn,
          user_answer_corrected: localResult.isClearCorrect ? body.userAnswer : card.expectedAnswerEn,
          feedback_pt: localResult.isClearCorrect
            ? "Resposta correta. Validacao local aplicada sem custo de IA."
            : "Resposta incorreta pela validacao local.",
          grammar_tip_pt: card.explanationPt,
          alternative_answers: alternatives
        };

    const nextReviewAt = getNextReviewDate(body.difficulty as ReviewDifficulty);
    const intervalDays = getNextIntervalDays(body.difficulty as ReviewDifficulty);

    await prisma.$transaction([
      prisma.review.create({
        data: {
          cardId: card.id,
          userId: user.id,
          userAnswer: body.userAnswer,
          correctedAnswer: feedback.correct_answer,
          aiFeedbackPt: feedback.feedback_pt,
          grammarTipPt: feedback.grammar_tip_pt,
          score: feedback.score,
          wasCorrect: feedback.is_correct,
          difficultyRating: body.difficulty,
          nextReviewAt
        }
      }),
      prisma.card.update({
        where: { id: card.id },
        data: {
          nextReviewAt,
          intervalDays,
          reviewCount: { increment: 1 }
        }
      })
    ]);

    return NextResponse.json({
      feedback: {
        isCorrect: feedback.is_correct,
        score: feedback.score,
        correctedAnswer: feedback.correct_answer,
        feedbackPt: feedback.feedback_pt,
        grammarTipPt: feedback.grammar_tip_pt,
        alternatives: feedback.alternative_answers
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Erro ao revisar card.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { getOrCreateDefaultUser } from "@/lib/default-user";

const createDeckSchema = z.object({
  name: z.string().min(2),
  theme: z.string().min(2),
  level: z.string().min(2),
  description: z.string().optional()
});

export async function GET() {
  const decks = await prisma.deck.findMany({
    orderBy: { createdAt: "desc" },
    include: { _count: { select: { cards: true } } }
  });
  return NextResponse.json({ decks });
}

export async function POST(request: NextRequest) {
  try {
    const body = createDeckSchema.parse(await request.json());
    const user = await getOrCreateDefaultUser();
    const deck = await prisma.deck.create({
      data: {
        name: body.name,
        theme: body.theme,
        level: body.level,
        description: body.description,
        userId: user.id
      }
    });
    return NextResponse.json({ deckId: deck.id }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Erro ao criar deck.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

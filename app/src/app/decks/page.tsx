import Link from "next/link";
import { prisma } from "@/lib/prisma";

export default async function DecksPage() {
  const decks = await prisma.deck.findMany({
    orderBy: { createdAt: "desc" },
    include: { _count: { select: { cards: true } } }
  });

  return (
    <section className="grid">
      <article className="card">
        <h1>Decks</h1>
        <Link href="/decks/new">Criar deck</Link>
      </article>
      {decks.map((deck) => (
        <article key={deck.id} className="card">
          <h3>{deck.name}</h3>
          <p>Tema: {deck.theme}</p>
          <p>Nivel: {deck.level}</p>
          <p>Cards: {deck._count.cards}</p>
        </article>
      ))}
    </section>
  );
}

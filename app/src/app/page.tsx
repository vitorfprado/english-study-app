import { prisma } from "@/lib/prisma";

export default async function DashboardPage() {
  const [decks, dueCards, todayReviews] = await Promise.all([
    prisma.deck.count(),
    prisma.card.count({ where: { nextReviewAt: { lte: new Date() } } }),
    prisma.review.count({
      where: { reviewedAt: { gte: new Date(new Date().setHours(0, 0, 0, 0)) } }
    })
  ]);

  return (
    <section className="grid">
      <article className="card">
        <h1>Dashboard</h1>
        <p>Total de decks: {decks}</p>
        <p>Cards pendentes: {dueCards}</p>
        <p>Cards revisados hoje: {todayReviews}</p>
      </article>
    </section>
  );
}

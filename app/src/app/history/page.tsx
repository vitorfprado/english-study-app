import { prisma } from "@/lib/prisma";

export default async function HistoryPage() {
  const reviews = await prisma.review.findMany({
    orderBy: { reviewedAt: "desc" },
    take: 30,
    include: { card: true }
  });

  return (
    <section className="grid">
      <article className="card">
        <h1>Historico</h1>
        <p>Ultimas 30 revisoes.</p>
      </article>
      {reviews.map((review) => (
        <article className="card" key={review.id}>
          <p>Frase: {review.card.sourceTextPt}</p>
          <p>Sua resposta: {review.userAnswer}</p>
          <p>Correta: {review.correctedAnswer}</p>
          <p>Feedback: {review.aiFeedbackPt}</p>
          <p>Score: {review.score}</p>
        </article>
      ))}
    </section>
  );
}

"use client";

import { useEffect, useState } from "react";

type DueCard = {
  id: string;
  sourceTextPt: string;
};

type ReviewResponse = {
  feedback: {
    isCorrect: boolean;
    score: number;
    correctedAnswer: string;
    feedbackPt: string;
    grammarTipPt: string;
    alternatives: string[];
  };
};

export default function ReviewPage() {
  const [card, setCard] = useState<DueCard | null>(null);
  const [answer, setAnswer] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [result, setResult] = useState<ReviewResponse | null>(null);

  useEffect(() => {
    fetch("/api/review")
      .then((res) => res.json())
      .then((data) => setCard(data.card ?? null));
  }, []);

  async function submitReview() {
    if (!card || !answer) return;
    const response = await fetch("/api/review", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        cardId: card.id,
        userAnswer: answer,
        difficulty
      })
    });
    const data = await response.json();
    setResult(data);
  }

  if (!card) return <section className="card">Sem cards pendentes agora.</section>;

  return (
    <section className="card">
      <h1>Revisao</h1>
      <p>Traduza para ingles:</p>
      <h3>{card.sourceTextPt}</h3>
      <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} />
      <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
        <option value="wrong">Errei</option>
        <option value="hard">Dificil</option>
        <option value="medium">Medio</option>
        <option value="easy">Facil</option>
      </select>
      <button onClick={submitReview}>Responder</button>
      {result && (
        <article className="card">
          <p>Correta: {result.feedback.isCorrect ? "Sim" : "Nao"}</p>
          <p>Score: {result.feedback.score}</p>
          <p>Correcao: {result.feedback.correctedAnswer}</p>
          <p>Feedback: {result.feedback.feedbackPt}</p>
          <p>Dica: {result.feedback.grammarTipPt}</p>
          {!!result.feedback.alternatives.length && (
            <p>Alternativas: {result.feedback.alternatives.join(" | ")}</p>
          )}
        </article>
      )}
    </section>
  );
}

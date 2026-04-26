export type ReviewDifficulty = "wrong" | "hard" | "medium" | "easy";

export function getNextIntervalDays(difficulty: ReviewDifficulty): number {
  switch (difficulty) {
    case "wrong":
      return 1;
    case "hard":
      return 1;
    case "medium":
      return 3;
    case "easy":
      return 7;
    default:
      return 1;
  }
}

export function getNextReviewDate(difficulty: ReviewDifficulty): Date {
  const now = new Date();
  if (difficulty === "wrong") {
    return new Date(now.getTime() + 10 * 60 * 1000);
  }

  const days = getNextIntervalDays(difficulty);
  return new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
}

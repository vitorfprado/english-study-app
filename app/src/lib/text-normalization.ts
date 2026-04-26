export function normalizeEnglishText(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^\w\s']/g, "")
    .replace(/\s+/g, " ");
}

export function jaccardSimilarity(a: string, b: string): number {
  const tokensA = new Set(normalizeEnglishText(a).split(" ").filter(Boolean));
  const tokensB = new Set(normalizeEnglishText(b).split(" ").filter(Boolean));

  if (!tokensA.size && !tokensB.size) return 1;
  if (!tokensA.size || !tokensB.size) return 0;

  const intersection = [...tokensA].filter((token) => tokensB.has(token)).length;
  const union = new Set([...tokensA, ...tokensB]).size;

  return union === 0 ? 0 : intersection / union;
}

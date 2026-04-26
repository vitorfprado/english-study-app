import { AIProvider } from "./ai-provider";
import { ClaudeProvider } from "./claude-provider";

export function getAIProvider(): AIProvider {
  const provider = process.env.AI_PROVIDER ?? "claude";
  if (provider !== "claude") {
    throw new Error(`AI provider '${provider}' ainda nao implementado.`);
  }

  const apiKey = process.env.CLAUDE_API_KEY;
  if (!apiKey) {
    throw new Error("CLAUDE_API_KEY nao configurada.");
  }

  return new ClaudeProvider(apiKey);
}

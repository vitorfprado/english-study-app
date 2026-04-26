"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function NewDeckPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(formData: FormData) {
    setLoading(true);
    setError(null);

    try {
      const payload = {
        name: String(formData.get("name") ?? ""),
        theme: String(formData.get("theme") ?? ""),
        level: String(formData.get("level") ?? "A1"),
        quantity: Number(formData.get("quantity") ?? 10),
        grammarFocus: String(formData.get("grammarFocus") ?? ""),
        description: String(formData.get("description") ?? "")
      };

      const response = await fetch("/api/decks/generate", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error("Falha ao criar deck com IA.");
      }

      router.push("/decks");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h1>Criar deck com IA</h1>
      <form action={handleSubmit} className="grid">
        <input name="name" placeholder="Nome do deck" required />
        <input name="theme" placeholder="Tema" required />
        <select name="level" defaultValue="A1">
          <option value="A1">A1</option>
          <option value="A2">A2</option>
          <option value="B1">B1</option>
          <option value="B2">B2</option>
        </select>
        <input name="quantity" type="number" min={1} max={50} defaultValue={10} required />
        <input name="grammarFocus" placeholder="Foco gramatical ou vocabulario" required />
        <textarea name="description" placeholder="Descricao opcional" />
        <button type="submit" disabled={loading}>
          {loading ? "Gerando..." : "Gerar cards"}
        </button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </section>
  );
}

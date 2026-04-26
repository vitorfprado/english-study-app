import "./globals.css";
import Link from "next/link";
import { ReactNode } from "react";

export const metadata = {
  title: "English Study App",
  description: "Estudo de ingles com repeticao espacada + IA"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <main>
          <nav className="card">
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link href="/">Dashboard</Link>
              <Link href="/decks">Decks</Link>
              <Link href="/review">Revisao</Link>
              <Link href="/history">Historico</Link>
            </div>
          </nav>
          {children}
        </main>
      </body>
    </html>
  );
}

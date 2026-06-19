import { useState } from "react";
import type { ReactNode } from "react";

function renderInline(text: string): ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) =>
    p.startsWith("**") && p.endsWith("**")
      ? <strong key={i} className="font-semibold text-gray-800">{p.slice(2, -2)}</strong>
      : p
  );
}

function MarkdownAnswer({ text }: { text: string }) {
  const lines = text.split("\n");
  const nodes: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (/^###\s/.test(line)) {
      nodes.push(<p key={i} className="font-semibold text-gray-700 mt-2">{renderInline(line.slice(4))}</p>);
    } else if (/^##\s/.test(line)) {
      nodes.push(<p key={i} className="font-bold text-gray-800 mt-3">{renderInline(line.slice(3))}</p>);
    } else if (/^#\s/.test(line)) {
      nodes.push(<p key={i} className="font-bold text-gray-900 mt-1 mb-1">{renderInline(line.slice(2))}</p>);
    } else if (/^[-*]\s/.test(line)) {
      nodes.push(
        <div key={i} className="flex gap-2 ml-2">
          <span className="text-indigo-400 mt-0.5">•</span>
          <span>{renderInline(line.slice(2))}</span>
        </div>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const num = line.match(/^(\d+)\.\s/)![1];
      nodes.push(
        <div key={i} className="flex gap-2 ml-2">
          <span className="text-indigo-400 font-mono text-xs mt-0.5 w-4 shrink-0">{num}.</span>
          <span>{renderInline(line.replace(/^\d+\.\s/, ""))}</span>
        </div>
      );
    } else if (line.trim() === "") {
      nodes.push(<div key={i} className="h-1.5" />);
    } else {
      nodes.push(<p key={i}>{renderInline(line)}</p>);
    }
    i++;
  }

  return <div className="text-sm text-gray-700 leading-relaxed space-y-0.5">{nodes}</div>;
}
import { askQuestion } from "../api/client";

interface QA {
  question: string;
  answer: string;
}

const SUGGESTIONS = [
  "¿Cuáles son los problemas más críticos esta semana?",
  "¿Qué producto genera más quejas?",
  "¿Cuánto tiempo demora en promedio resolver un ticket?",
  "¿Cuáles son los tickets con clientes más frustrados?",
];

export function AskBar() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<QA[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(q?: string) {
    const text = (q ?? question).trim();
    if (!text) return;

    setLoading(true);
    setError(null);
    try {
      const result = await askQuestion(text);
      setHistory((prev) => [{ question: result.question, answer: result.answer }, ...prev].slice(0, 5));
      setQuestion("");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Error al conectar con el backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-4">
      <h3 className="text-sm font-semibold text-gray-700">Pregunta en lenguaje natural</h3>

      {/* Sugerencias */}
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSubmit(s)}
            disabled={loading}
            className="text-xs px-3 py-1.5 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded-full hover:bg-indigo-100 transition-colors disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Escribe tu pregunta sobre los tickets..."
          className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          disabled={loading}
        />
        <button
          onClick={() => handleSubmit()}
          disabled={loading || !question.trim()}
          className="px-4 py-2.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors whitespace-nowrap"
        >
          {loading ? "Analizando..." : "Preguntar"}
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Historial de respuestas */}
      {history.map((qa, i) => (
        <div key={i} className="border border-gray-100 rounded-xl overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 text-xs font-medium text-gray-500 border-b border-gray-100">
            {qa.question}
          </div>
          <div className="px-4 py-3">
            <MarkdownAnswer text={qa.answer} />
          </div>
        </div>
      ))}
    </div>
  );
}

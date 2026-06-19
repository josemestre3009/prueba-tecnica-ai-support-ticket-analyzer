import type { StatusResponse, SummaryResponse } from "../types/ticket";

interface CardProps {
  title: string;
  value: string | number;
  sub?: string;
  alert?: boolean;
}

function Card({ title, value, sub, alert }: CardProps) {
  return (
    <div
      className={`rounded-xl border p-5 shadow-sm bg-white flex flex-col gap-1 ${
        alert ? "border-red-300 bg-red-50" : "border-gray-200"
      }`}
    >
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{title}</span>
      <span className={`text-3xl font-bold ${alert ? "text-red-600" : "text-gray-900"}`}>
        {value}
      </span>
      {sub && <span className="text-sm text-gray-400">{sub}</span>}
    </div>
  );
}

interface Props {
  summary: SummaryResponse;
  status: StatusResponse;
}

export function KPICards({ summary, status }: Props) {
  const topCategory =
    Object.entries(summary.por_categoria_ia).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "N/A";

  const topPriority =
    Object.entries(summary.por_prioridad).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "N/A";

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <Card
        title="Total tickets"
        value={summary.total_tickets.toLocaleString()}
        sub="en base de datos"
      />
      <Card
        title="Analizados por IA"
        value={`${status.progreso_pct}%`}
        sub={`${status.procesados_ok} / ${summary.total_tickets}`}
      />
      <Card
        title="Críticos / Altos abiertos"
        value={summary.tickets_criticos_abiertos}
        sub="sin resolver"
        alert={summary.tickets_criticos_abiertos > 0}
      />
      <Card
        title="Rating promedio"
        value={summary.rating_promedio != null ? summary.rating_promedio.toFixed(1) + " / 5" : "N/A"}
        sub="satisfacción cliente"
      />
      <Card
        title="Categoría top (IA)"
        value={topCategory}
        sub="más frecuente"
      />
      <Card
        title="Prioridad top"
        value={topPriority}
        sub="distribución original"
      />
    </div>
  );
}

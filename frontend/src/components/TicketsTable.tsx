import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTickets } from "../api/client";
import type { TicketFilters } from "../types/ticket";

const PRIORITY_BADGE: Record<string, string> = {
  Critical: "bg-red-100 text-red-700",
  High: "bg-orange-100 text-orange-700",
  Medium: "bg-yellow-100 text-yellow-700",
  Low: "bg-green-100 text-green-700",
};

const STATUS_BADGE: Record<string, string> = {
  Open: "bg-blue-100 text-blue-700",
  "Pending Customer Response": "bg-purple-100 text-purple-700",
  Closed: "bg-gray-100 text-gray-600",
};

const SENTIMENT_BADGE: Record<string, string> = {
  Frustrated: "bg-red-100 text-red-600",
  Urgent: "bg-orange-100 text-orange-600",
  Confused: "bg-yellow-100 text-yellow-700",
  Neutral: "bg-gray-100 text-gray-600",
  Satisfied: "bg-green-100 text-green-700",
};

function Badge({ value, map }: { value: string | null; map: Record<string, string> }) {
  if (!value) return <span className="text-gray-300">—</span>;
  const cls = map[value] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {value}
    </span>
  );
}

const STATUSES = ["Open", "Pending Customer Response", "Closed"];
const PRIORITIES = ["Critical", "High", "Medium", "Low"];
const SENTIMENTS = ["Frustrated", "Urgent", "Confused", "Neutral", "Satisfied"];
const CATEGORIES = ["Hardware", "Software", "Billing", "Cancellation", "Product Inquiry", "Network", "Other"];

interface TooltipState { text: string; x: number; y: number }

export function TicketsTable() {
  const [filters, setFilters] = useState<Partial<TicketFilters>>({
    page: 1,
    page_size: 50,
  });
  const [expanded, setExpanded] = useState<number | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["tickets", filters],
    queryFn: () => getTickets(filters),
    placeholderData: (prev) => prev,
  });

  const totalPages = data ? Math.ceil(data.total / (filters.page_size ?? 50)) : 1;

  function setFilter(key: keyof TicketFilters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
  }

  function clearFilters() {
    setFilters({ page: 1, page_size: 50 });
  }

  return (
    <>
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Filtros */}
      <div className="p-4 border-b border-gray-100 flex flex-wrap gap-3 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Estado</label>
          <select
            className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            value={filters.status ?? ""}
            onChange={(e) => setFilter("status", e.target.value)}
          >
            <option value="">Todos</option>
            {STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Prioridad</label>
          <select
            className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            value={filters.priority ?? ""}
            onChange={(e) => setFilter("priority", e.target.value)}
          >
            <option value="">Todas</option>
            {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Categoría IA</label>
          <select
            className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            value={filters.ai_category ?? ""}
            onChange={(e) => setFilter("ai_category", e.target.value)}
          >
            <option value="">Todas</option>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Sentimiento IA</label>
          <select
            className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            value={filters.ai_sentiment ?? ""}
            onChange={(e) => setFilter("ai_sentiment", e.target.value)}
          >
            <option value="">Todos</option>
            {SENTIMENTS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1 flex-1 min-w-[180px]">
          <label className="text-xs text-gray-500">Buscar</label>
          <input
            type="text"
            placeholder="Producto o descripción..."
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            value={filters.search ?? ""}
            onChange={(e) => setFilter("search", e.target.value)}
          />
        </div>

        <button
          onClick={clearFilters}
          className="px-3 py-1.5 text-sm text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          Limpiar
        </button>

        <span className="ml-auto text-sm text-gray-400 self-end">
          {isLoading ? "Cargando..." : `${data?.total ?? 0} resultados`}
        </span>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              {["ID", "Cliente", "Producto", "Estado", "Prior.", "Cat. IA", "Prior. IA", "Sentimiento", "Equipo IA", "Resumen IA"].map(
                (h) => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={10} className="text-center py-10 text-gray-400">
                  Cargando tickets...
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={10} className="text-center py-10 text-red-400">
                  Error al cargar los tickets. ¿Está el backend corriendo?
                </td>
              </tr>
            )}
            {data?.data.map((ticket) => (
              <>
                <tr
                  key={ticket.ticket_id}
                  className="border-b border-gray-50 hover:bg-indigo-50 cursor-pointer transition-colors"
                  onClick={() => setExpanded(expanded === ticket.ticket_id ? null : ticket.ticket_id)}
                >
                  <td className="px-3 py-2.5 font-mono text-xs text-gray-400">{ticket.ticket_id}</td>
                  <td className="px-3 py-2.5 whitespace-nowrap">{ticket.customer_name ?? "—"}</td>
                  <td className="px-3 py-2.5 whitespace-nowrap text-gray-600">{ticket.product_purchased ?? "—"}</td>
                  <td className="px-3 py-2.5">
                    <Badge value={ticket.ticket_status} map={STATUS_BADGE} />
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge value={ticket.ticket_priority} map={PRIORITY_BADGE} />
                  </td>
                  <td className="px-3 py-2.5 text-gray-600">{ticket.ai_category ?? "—"}</td>
                  <td className="px-3 py-2.5">
                    <Badge value={ticket.ai_priority} map={PRIORITY_BADGE} />
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge value={ticket.ai_sentiment} map={SENTIMENT_BADGE} />
                  </td>
                  <td className="px-3 py-2.5 text-gray-600 whitespace-nowrap">{ticket.ai_responsible_team ?? "—"}</td>
                  <td
                    className="px-3 py-2.5 max-w-sm"
                    onMouseEnter={(e) => ticket.ai_summary && setTooltip({
                      text: ticket.ai_summary,
                      x: e.clientX,
                      y: e.clientY,
                    })}
                    onMouseMove={(e) => tooltip && setTooltip((t) => t ? { ...t, x: e.clientX, y: e.clientY } : null)}
                    onMouseLeave={() => setTooltip(null)}
                  >
                    <p className="text-xs text-gray-500 italic leading-relaxed line-clamp-2 cursor-default">
                      {ticket.ai_summary ?? <span className="not-italic text-gray-300">Sin analizar</span>}
                    </p>
                  </td>
                </tr>
                {expanded === ticket.ticket_id && (
                  <tr key={`exp-${ticket.ticket_id}`}>
                    <td colSpan={10} className="px-4 pb-3 pt-0 bg-white">
                      <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-5 grid grid-cols-3 gap-5">

                        {/* Descripción original */}
                        <div className="col-span-2 flex flex-col gap-2">
                          <p className="text-xs font-semibold text-indigo-500 uppercase tracking-wide">Descripción original</p>
                          <p className="text-sm text-gray-600 leading-relaxed bg-white rounded-lg border border-gray-100 px-4 py-3">
                            {ticket.ticket_description ?? <span className="text-gray-300 italic">Sin descripción</span>}
                          </p>
                          {ticket.has_template_placeholders && (
                            <span className="self-start bg-yellow-50 border border-yellow-200 text-yellow-700 text-xs px-2.5 py-1 rounded-full">
                              ⚠ Contiene placeholders sin resolver
                            </span>
                          )}
                          {ticket.ai_error && (
                            <span className="self-start bg-red-50 border border-red-200 text-red-600 text-xs px-2.5 py-1 rounded-full">
                              Error IA: {ticket.ai_error}
                            </span>
                          )}
                        </div>

                        {/* Detalles en grid 2×N */}
                        <div className="flex flex-col gap-3">
                          <p className="text-xs font-semibold text-indigo-500 uppercase tracking-wide">Datos del cliente</p>
                          <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                            {[
                              ["Email", ticket.customer_email],
                              ["Edad", ticket.customer_age],
                              ["Género", ticket.customer_gender],
                              ["Canal", ticket.ticket_channel],
                              ["Tipo", ticket.ticket_type],
                              ["Fecha compra", ticket.date_of_purchase],
                              ["1ª respuesta", ticket.first_response_time
                                ? new Date(ticket.first_response_time).toLocaleDateString("es")
                                : null],
                              ["Resolución", ticket.time_to_resolution
                                ? new Date(ticket.time_to_resolution).toLocaleDateString("es")
                                : null],
                              ["Rating", ticket.satisfaction_rating != null
                                ? `${ticket.satisfaction_rating} / 5`
                                : null],
                            ].map(([label, value]) => (
                              <div key={String(label)}>
                                <p className="text-xs text-gray-400 leading-none mb-0.5">{label}</p>
                                <p className="text-gray-700 font-medium truncate">
                                  {value != null && value !== "" ? String(value) : <span className="text-gray-300 font-normal">—</span>}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>

                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
        <button
          disabled={!filters.page || filters.page <= 1}
          onClick={() => setFilters((p) => ({ ...p, page: (p.page ?? 1) - 1 }))}
          className="px-3 py-1 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
        >
          Anterior
        </button>
        <span className="text-sm text-gray-400">
          Página {filters.page ?? 1} de {totalPages}
        </span>
        <button
          disabled={(filters.page ?? 1) >= totalPages}
          onClick={() => setFilters((p) => ({ ...p, page: (p.page ?? 1) + 1 }))}
          className="px-3 py-1 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
        >
          Siguiente
        </button>
      </div>
    </div>
    {tooltip && (
      <div
        className="fixed z-[9999] pointer-events-none max-w-sm bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-xl leading-relaxed"
        style={{ top: tooltip.y - 12, left: tooltip.x + 12, transform: "translateY(-100%)" }}
      >
        {tooltip.text}
      </div>
    )}
    </>
  );
}

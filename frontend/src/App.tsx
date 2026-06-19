import { useQuery } from "@tanstack/react-query";
import { getSummary, getStatus } from "./api/client";
import { KPICards } from "./components/KPICards";
import { Charts } from "./components/Charts";
import { TicketsTable } from "./components/TicketsTable";
import { AskBar } from "./components/AskBar";
import { ProcessingBanner } from "./components/ProcessingBanner";

export default function App() {
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["summary"],
    queryFn: getSummary,
    refetchInterval: 10000,
  });

  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: getStatus,
    refetchInterval: 5000,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <div>
          <h1 className="text-base font-semibold text-gray-900">AI Support Ticket Analyzer</h1>
          <p className="text-xs text-gray-400">Análisis automático de tickets con IA</p>
        </div>
        {status && (
          <div className="ml-auto flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status.en_curso ? "bg-blue-500 animate-pulse" : "bg-green-400"}`} />
            <span className="text-xs text-gray-500">
              {status.en_curso ? "Procesando..." : `${status.procesados_ok} analizados`}
            </span>
          </div>
        )}
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-6 flex flex-col gap-6">
        {/* Banner de progreso */}
        <ProcessingBanner />

        {/* KPIs */}
        {loadingSummary ? (
          <div className="h-24 bg-white rounded-xl border border-gray-200 animate-pulse" />
        ) : summary && status ? (
          <KPICards summary={summary} status={status} />
        ) : null}

        {/* Gráficos */}
        {summary && <Charts summary={summary} />}

        {/* Pregunta en lenguaje natural */}
        <AskBar />

        {/* Tabla de tickets */}
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Tickets</h2>
          <TicketsTable />
        </div>
      </main>
    </div>
  );
}

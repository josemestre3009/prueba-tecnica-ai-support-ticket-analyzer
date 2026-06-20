import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getStatus, triggerProcess, triggerReprocess } from "../api/client";
import { useState, useEffect, useRef } from "react";

export function ProcessingBanner() {
  const [triggered, setTriggered] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const queryClient = useQueryClient();
  const wasProcessing = useRef(false);

  const { data: status, refetch } = useQuery({
    queryKey: ["status"],
    queryFn: getStatus,
    refetchInterval: (query) => (query.state.data?.en_curso ? 3000 : 10000),
  });

  // Cuando el procesamiento termina, refrescar tickets y summary automáticamente
  useEffect(() => {
    if (wasProcessing.current && status && !status.en_curso) {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      setTriggered(false);
    }
    wasProcessing.current = status?.en_curso ?? false;
  }, [status?.en_curso, queryClient]);

  async function handleProcess() {
    setTriggered(true);
    await triggerProcess();
    refetch();
  }

  async function handleReprocess() {
    if (!confirming) {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 4000);
      return;
    }
    setConfirming(false);
    setTriggered(true);
    await triggerReprocess();
    refetch();
  }

  if (!status) return null;

  const isDone = status.progreso_pct === 100 && !status.en_curso;

  return (
    <div className={`rounded-xl border p-4 flex items-center gap-3 ${
      status.en_curso
        ? "bg-blue-50 border-blue-200"
        : isDone
        ? "bg-gray-50 border-gray-200"
        : "bg-amber-50 border-amber-200"
    }`}>
      <div className="flex-1">
        {status.en_curso ? (
          <>
            <p className="text-sm font-medium text-blue-700">
              Analizando tickets con IA… {status.progreso_pct}%
            </p>
            <div className="mt-2 bg-blue-100 rounded-full h-2 overflow-hidden">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${status.progreso_pct}%` }}
              />
            </div>
            <p className="text-xs text-blue-500 mt-1">
              {status.procesados_ok} procesados · {status.pendientes} pendientes
              {status.con_error > 0 && ` · ${status.con_error} con error`}
            </p>
          </>
        ) : isDone ? (
          <p className="text-sm font-medium text-gray-600">
            ✓ {status.procesados_ok} tickets analizados por IA.
          </p>
        ) : (
          <p className="text-sm font-medium text-amber-700">
            {status.pendientes} tickets pendientes de análisis IA.
          </p>
        )}
      </div>

      <div className="flex gap-2 shrink-0">
        {!status.en_curso && status.pendientes > 0 && (
          <button
            onClick={handleProcess}
            disabled={triggered}
            className="px-3 py-1.5 bg-amber-500 text-white text-sm rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors whitespace-nowrap"
          >
            {triggered ? "Iniciando…" : "Analizar pendientes"}
          </button>
        )}

        {!status.en_curso && (
          <button
            onClick={handleReprocess}
            disabled={triggered}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors whitespace-nowrap disabled:opacity-50 ${
              confirming
                ? "bg-red-500 text-white border-red-500 hover:bg-red-600"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
            }`}
          >
            {confirming ? "¿Confirmar reanalizar todo?" : "Reanalizar todo"}
          </button>
        )}
      </div>
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import { getStatus, triggerProcess } from "../api/client";
import { useState } from "react";

export function ProcessingBanner() {
  const [triggered, setTriggered] = useState(false);

  const { data: status, refetch } = useQuery({
    queryKey: ["status"],
    queryFn: getStatus,
    refetchInterval: (query) => {
      return query.state.data?.en_curso ? 3000 : false;
    },
  });

  async function handleProcess() {
    setTriggered(true);
    await triggerProcess();
    refetch();
  }

  if (!status) return null;
  if (status.progreso_pct === 100 && !status.en_curso) return null;

  return (
    <div className={`rounded-xl border p-4 flex items-center gap-4 ${
      status.en_curso
        ? "bg-blue-50 border-blue-200"
        : "bg-amber-50 border-amber-200"
    }`}>
      <div className="flex-1">
        {status.en_curso ? (
          <>
            <p className="text-sm font-medium text-blue-700">
              Analizando tickets con IA... {status.progreso_pct}%
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
        ) : (
          <p className="text-sm font-medium text-amber-700">
            {status.pendientes} tickets pendientes de análisis IA.
          </p>
        )}
      </div>

      {!status.en_curso && status.pendientes > 0 && (
        <button
          onClick={handleProcess}
          disabled={triggered}
          className="px-4 py-2 bg-amber-500 text-white text-sm rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors whitespace-nowrap"
        >
          {triggered ? "Iniciando..." : "Iniciar análisis IA"}
        </button>
      )}
    </div>
  );
}

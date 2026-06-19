import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SummaryResponse } from "../types/ticket";

const PRIORITY_COLORS: Record<string, string> = {
  Critical: "#ef4444",
  High: "#f97316",
  Medium: "#eab308",
  Low: "#22c55e",
};

const CATEGORY_COLORS = [
  "#6366f1", "#8b5cf6", "#ec4899", "#14b8a6", "#f59e0b", "#3b82f6", "#10b981",
];

const SENTIMENT_COLORS: Record<string, string> = {
  Frustrated: "#ef4444",
  Urgent: "#f97316",
  Confused: "#eab308",
  Neutral: "#6b7280",
  Satisfied: "#22c55e",
};

interface Props {
  summary: SummaryResponse;
}

export function Charts({ summary }: Props) {
  const categoryData = Object.entries(summary.por_categoria_ia)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const priorityData = Object.entries(summary.por_prioridad).map(([name, value]) => ({
    name,
    value,
    fill: PRIORITY_COLORS[name] ?? "#6b7280",
  }));

  const sentimentData = Object.entries(summary.por_sentimiento_ia).map(([name, value]) => ({
    name,
    value,
    fill: SENTIMENT_COLORS[name] ?? "#6b7280",
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Barras — categorías IA */}
      <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Tickets por categoría (IA)</h3>
        {categoryData.length === 0 ? (
          <p className="text-gray-400 text-sm">Sin datos — ejecuta el análisis IA primero.</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={categoryData} layout="vertical" margin={{ left: 20, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} width={110} />
              <Tooltip />
              <Bar dataKey="value" name="Tickets" radius={[0, 4, 4, 0]}>
                {categoryData.map((_, i) => (
                  <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Donuts — prioridad y sentimiento */}
      <div className="flex flex-col gap-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Prioridad</h3>
          {priorityData.length === 0 ? (
            <p className="text-gray-400 text-sm">Sin datos</p>
          ) : (
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={priorityData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  paddingAngle={2}
                >
                  {priorityData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Sentimiento (IA)</h3>
          {sentimentData.length === 0 ? (
            <p className="text-gray-400 text-sm">Sin datos — ejecuta el análisis IA primero.</p>
          ) : (
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  paddingAngle={2}
                >
                  {sentimentData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie,
  Legend,
} from "recharts";
import { fundPerformanceData, sectorAllocation } from "@/lib/mock-data";

export function FundPerformanceChart() {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <h3 className="text-sm font-semibold text-foreground mb-1">
        Fund TVPI Performance
      </h3>
      <p className="text-xs text-muted mb-4">Quarterly TVPI trajectory</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={fundPerformanceData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis
            dataKey="quarter"
            tick={{ fontSize: 11, fill: "#737373" }}
            axisLine={{ stroke: "#e5e5e5" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#737373" }}
            axisLine={{ stroke: "#e5e5e5" }}
            tickLine={false}
            domain={[0.9, 2.5]}
            tickFormatter={(v: number) => `${v.toFixed(1)}x`}
          />
          <Tooltip
            contentStyle={{
              background: "#fff",
              border: "1px solid #e5e5e5",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            formatter={(value) => [`${Number(value).toFixed(2)}x`, ""]}
          />
          <Line
            type="monotone"
            dataKey="fundIII"
            stroke="#2563eb"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#2563eb" }}
            name="Fund III"
          />
          <Line
            type="monotone"
            dataKey="fundII"
            stroke="#111111"
            strokeWidth={2}
            dot={{ r: 3, fill: "#111111" }}
            name="Fund II"
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            stroke="#a3a3a3"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
            name="Benchmark"
          />
          <Legend
            iconType="line"
            wrapperStyle={{ fontSize: "11px", color: "#737373" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SectorAllocationChart() {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <h3 className="text-sm font-semibold text-foreground mb-1">
        Sector Allocation
      </h3>
      <p className="text-xs text-muted mb-4">Current portfolio by sector</p>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={sectorAllocation}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
            stroke="none"
          >
            {sectorAllocation.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#fff",
              border: "1px solid #e5e5e5",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            formatter={(value) => [`${value}%`, ""]}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: "11px", color: "#737373" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MiniSparkline({
  data,
  color = "#2563eb",
  height = 40,
}: {
  data: number[];
  color?: string;
  height?: number;
}) {
  const chartData = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function DealStageChart({ stageCounts }: { stageCounts: { stage: string; count: number }[] }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <h3 className="text-sm font-semibold text-foreground mb-1">
        Pipeline by Stage
      </h3>
      <p className="text-xs text-muted mb-4">Active deals across stages</p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={stageCounts} barSize={32}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
          <XAxis
            dataKey="stage"
            tick={{ fontSize: 10, fill: "#737373" }}
            axisLine={{ stroke: "#e5e5e5" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#737373" }}
            axisLine={{ stroke: "#e5e5e5" }}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              background: "#fff",
              border: "1px solid #e5e5e5",
              borderRadius: "8px",
              fontSize: "12px",
            }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {stageCounts.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={index < stageCounts.length - 1 ? "#2563eb" : "#111111"}
                opacity={0.15 + (index / stageCounts.length) * 0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

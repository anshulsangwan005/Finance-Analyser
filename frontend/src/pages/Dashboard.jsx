import React, { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, inr, thisMonth } from "../api.js";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7", "#ec4899", "#84cc16", "#f97316", "#14b8a6", "#64748b", "#eab308"];

const Stat = ({ label, value, tone = "" }) => (
  <div className="card"><p className="text-xs uppercase text-slate-500">{label}</p><p className={`text-2xl font-bold ${tone}`}>{value}</p></div>
);

export default function Dashboard() {
  const [month, setMonth] = useState(thisMonth());
  const [s, setS] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    setErr("");
    Promise.all([api.summary(month), api.budgets(month)]).then(([a, b]) => { setS(a); setBudgets(b); }).catch((e) => setErr(e.message));
  }, [month]);

  if (err) return <p className="text-red-600">{err}</p>;
  if (!s) return <p className="text-slate-500">Loading…</p>;
  const alerts = budgets.filter((b) => b.level !== "ok");

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Dashboard</h2>
        <input type="month" className="input w-auto" value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>

      {alerts.map((b) => (
        <div key={b.category} className={`rounded-lg px-4 py-2 text-sm ${b.level === "exceeded" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-700"}`}>
          {b.level === "exceeded" ? "🚨" : "⚠️"} {b.category}: {inr(b.spent)} of {inr(b.limit)} ({b.pct}%)
        </div>
      ))}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Stat label="Income" value={inr(s.income)} tone="text-green-600" />
        <Stat label="Expenses" value={inr(s.expense)} tone="text-red-600" />
        <Stat label="Net savings" value={inr(s.savings)} tone={s.savings >= 0 ? "text-indigo-600" : "text-red-600"} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-medium mb-2">Spending by category</h3>
          {s.by_category.length === 0 ? <p className="text-sm text-slate-500">No expenses this month. Add or import transactions.</p> : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={s.by_category} dataKey="amount" nameKey="category" outerRadius={90} label={(e) => e.category}>
                  {s.by_category.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v) => inr(v)} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
        <div className="card">
          <h3 className="font-medium mb-2">Income vs expenses (last 6 months)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={s.trend}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis /><Tooltip formatter={(v) => inr(v)} /><Legend />
              <Bar dataKey="income" fill="#22c55e" /><Bar dataKey="expense" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

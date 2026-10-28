import React, { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, download, inr, thisMonth } from "../api.js";

const sev = { high: "bg-red-50 text-red-700", medium: "bg-amber-50 text-amber-700", info: "bg-indigo-50 text-indigo-700" };

export default function Insights() {
  const [fc, setFc] = useState(null);
  const [an, setAn] = useState([]);
  const [recs, setRecs] = useState(null);
  const [err, setErr] = useState("");
  const m = thisMonth();

  useEffect(() => {
    Promise.all([api.forecast(), api.anomalies(), api.recs(m)]).then(([a, b, c]) => { setFc(a); setAn(b); setRecs(c); }).catch((e) => setErr(e.message));
  }, []);

  const exp = async (fmt) => download(await api.exportFile(fmt), `transactions.${fmt}`);
  const wipe = async () => {
    if (confirm("Permanently delete your account and ALL data? This cannot be undone.")) {
      await api.deleteAccount(); localStorage.removeItem("token"); window.location.href = "/login";
    }
  };

  if (err) return <p className="text-red-600">{err}</p>;
  if (!recs) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-xl font-semibold">AI Insights</h2>
        <div className="flex gap-2"><button className="btn-ghost" onClick={() => exp("csv")}>Export CSV</button><button className="btn-ghost" onClick={() => exp("pdf")}>Export PDF</button></div>
      </div>

      <section className="card space-y-3">
        <h3 className="font-medium">Next month forecast</h3>
        {!fc.available ? <p className="text-sm text-slate-500">{fc.reason}</p> : (
          <>
            <p className="text-sm">Expected spending in <b>{fc.next_month}</b>: <b className="text-lg">{inr(fc.total.predicted)}</b>
              <span className="text-slate-500"> (range {inr(fc.total.low)} – {inr(fc.total.high)})</span></p>
            {fc.low_confidence && <p className="text-xs text-amber-700">Based on under 3 months of history, so treat this as a rough estimate.</p>}
            {fc.total.backtest_mape != null && <p className="text-xs text-slate-500">Backtest error (MAPE): {fc.total.backtest_mape}%</p>}
            <div className="grid lg:grid-cols-2 gap-4">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={fc.history}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis /><Tooltip formatter={(v) => inr(v)} />
                  <Line dataKey="total" stroke="#6366f1" strokeWidth={2} name="Monthly expenses" /></LineChart>
              </ResponsiveContainer>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={fc.categories.slice(0, 8)}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="category" tick={{ fontSize: 11 }} /><YAxis /><Tooltip formatter={(v) => inr(v)} /><Legend />
                  <Bar dataKey="last_month" fill="#94a3b8" name="Last month" /><Bar dataKey="predicted" fill="#6366f1" name="Forecast" /></BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </section>

      <section className="card space-y-2">
        <h3 className="font-medium">Recommendations</h3>
        {recs.recommendations.map((r, i) => (
          <div key={i} className={`rounded-lg px-4 py-2 text-sm ${sev[r.severity]}`}><b>{r.title}.</b> {r.message}</div>
        ))}
        <p className="text-xs text-slate-400">{recs.disclaimer}</p>
      </section>

      <section className="card">
        <h3 className="font-medium mb-2">Unusual &amp; duplicate transactions</h3>
        {an.length === 0 ? <p className="text-sm text-slate-500">Nothing suspicious found.</p> : (
          <ul className="divide-y text-sm">
            {an.map((t) => (
              <li key={t.id} className="py-2 flex justify-between gap-3">
                <span>{t.date} · {t.description} <span className="text-slate-500">— {t.reason}</span></span>
                <span className="font-medium">{inr(t.amount)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h3 className="font-medium mb-1">Privacy</h3>
        <p className="text-sm text-slate-500 mb-2">Your data is only used for your own analysis. You can delete everything at any time.</p>
        <button className="btn-ghost text-red-600" onClick={wipe}>Delete my account &amp; data</button>
      </section>
    </div>
  );
}

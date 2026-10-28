import React, { useEffect, useState } from "react";
import { CATEGORIES, api, inr, thisMonth } from "../api.js";

export default function Budgets() {
  const [month, setMonth] = useState(thisMonth());
  const [list, setList] = useState([]);
  const [cat, setCat] = useState(CATEGORIES[0]);
  const [limit, setLimit] = useState("");
  const [err, setErr] = useState("");

  const load = () => api.budgets(month).then(setList).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [month]);

  async function save(e) {
    e.preventDefault();
    setErr("");
    try { await api.setBudget(cat, parseFloat(limit)); setLimit(""); load(); } catch (ex) { setErr(ex.message); }
  }
  const remove = async (c) => { await api.deleteBudget(c); load(); };
  const color = { ok: "bg-green-500", warning: "bg-amber-500", exceeded: "bg-red-500" };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Monthly budgets</h2>
        <input type="month" className="input w-auto" value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>
      <form onSubmit={save} className="card flex flex-wrap gap-3 items-end">
        <select className="input w-auto" value={cat} onChange={(e) => setCat(e.target.value)}>{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select>
        <input className="input w-40" type="number" min="1" required placeholder="Monthly limit ₹" value={limit} onChange={(e) => setLimit(e.target.value)} />
        <button className="btn">Set budget</button>
        {err && <span className="text-sm text-red-600">{err}</span>}
      </form>
      <div className="grid gap-3">
        {list.length === 0 && <p className="text-sm text-slate-500">No budgets yet. Set one above.</p>}
        {list.map((b) => (
          <div key={b.category} className="card">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">{b.category}</span>
              <span>{inr(b.spent)} / {inr(b.limit)} ({b.pct}%) <button className="ml-3 text-red-500 text-xs" onClick={() => remove(b.category)}>Remove</button></span>
            </div>
            <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden"><div className={`h-full ${color[b.level]}`} style={{ width: `${Math.min(b.pct, 100)}%` }} /></div>
          </div>
        ))}
      </div>
    </div>
  );
}

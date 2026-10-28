import React, { useEffect, useState } from "react";
import { CATEGORIES, api, inr, thisMonth } from "../api.js";

const today = () => new Date().toISOString().slice(0, 10);

export default function Transactions() {
  const [rows, setRows] = useState([]);
  const [filters, setFilters] = useState({ month: thisMonth(), category: "", q: "" });
  const [form, setForm] = useState({ date: today(), description: "", amount: "", type: "expense" });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const load = () => {
    const p = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
    api.listTx(p).then(setRows).catch((e) => setErr(e.message));
  };
  useEffect(load, [filters]);

  const wrap = (fn) => async (...a) => { setErr(""); setMsg(""); try { await fn(...a); load(); } catch (e) { setErr(e.message); } };

  const add = wrap(async (e) => {
    e.preventDefault();
    await api.addTx({ ...form, amount: parseFloat(form.amount) });
    setForm({ ...form, description: "", amount: "" });
  });
  const upload = wrap(async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const r = await api.importCsv(file);
    setMsg(`Imported ${r.imported} transactions (${r.skipped} rows skipped). Showing all months — clear the month filter to see older rows.`);
    e.target.value = "";
  });
  const recat = wrap((id, category) => api.updateTx(id, { category }));
  const del = wrap((id) => api.deleteTx(id));

  return (
    <div className="space-y-5">
      <h2 className="text-xl font-semibold">Transactions</h2>

      <form onSubmit={add} className="card grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
        <input className="input" type="date" required value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
        <input className="input md:col-span-2" placeholder="Description (e.g. UPI/SWIGGY)" required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <input className="input" type="number" step="0.01" min="0.01" placeholder="Amount ₹" required value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
        <select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
          <option value="expense">Expense</option><option value="income">Income</option>
        </select>
        <button className="btn">Add</button>
        <p className="col-span-full text-xs text-slate-500">Category is auto-assigned by the ML model. You can correct it in the table; the app remembers your correction.</p>
      </form>

      <div className="card flex flex-wrap gap-3 items-center">
        <label className="btn cursor-pointer">Import CSV<input type="file" accept=".csv" hidden onChange={upload} /></label>
        <span className="text-xs text-slate-500">Needs date, description and amount (or debit/credit) columns.</span>
        <div className="flex-1" />
        <input type="month" className="input w-auto" value={filters.month} onChange={(e) => setFilters({ ...filters, month: e.target.value })} />
        <select className="input w-auto" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
          <option value="">All categories</option>{[...CATEGORIES, "Income"].map((c) => <option key={c}>{c}</option>)}
        </select>
        <input className="input w-40" placeholder="Search…" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
      </div>

      {msg && <p className="text-sm text-green-700">{msg}</p>}
      {err && <p className="text-sm text-red-600">{err}</p>}

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr><th className="p-3">Date</th><th>Description</th><th>Category</th><th className="text-right">Amount</th><th /></tr>
          </thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan="5" className="p-6 text-center text-slate-500">No transactions found.</td></tr>}
            {rows.map((t) => (
              <tr key={t.id} className="border-t border-slate-100">
                <td className="p-3 whitespace-nowrap">{t.date}</td>
                <td className="pr-3">
                  {t.description}
                  {t.is_anomaly && <span title={t.flag_reason} className="ml-2 text-xs bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">unusual</span>}
                  {t.is_duplicate && <span title={t.flag_reason} className="ml-2 text-xs bg-red-100 text-red-700 rounded px-1.5 py-0.5">duplicate?</span>}
                </td>
                <td>
                  {t.type === "income" ? <span className="text-green-700">Income</span> : (
                    <select className="border rounded px-1 py-0.5 text-xs" value={t.category} onChange={(e) => recat(t.id, e.target.value)}>
                      {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                    </select>
                  )}
                  {t.source === "csv" && t.type === "expense" && t.confidence < 0.6 && <span title="Low model confidence — please check" className="ml-1">❓</span>}
                </td>
                <td className={`text-right pr-3 font-medium ${t.type === "income" ? "text-green-600" : "text-slate-800"}`}>{t.type === "income" ? "+" : "-"}{inr(t.amount)}</td>
                <td className="pr-3"><button className="text-red-500 text-xs" onClick={() => confirm("Delete this transaction?") && del(t.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

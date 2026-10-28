import React, { useEffect, useState } from "react";
import { api, inr } from "../api.js";

export default function Goals() {
  const [goals, setGoals] = useState([]);
  const [f, setF] = useState({ name: "", target_amount: "", deadline: "" });
  const [err, setErr] = useState("");
  const load = () => api.goals().then(setGoals).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);

  async function add(e) {
    e.preventDefault();
    setErr("");
    try {
      await api.addGoal({ name: f.name, target_amount: parseFloat(f.target_amount), deadline: f.deadline || null });
      setF({ name: "", target_amount: "", deadline: "" });
      load();
    } catch (ex) { setErr(ex.message); }
  }
  const contribute = async (id) => {
    const v = prompt("Amount to add (₹):");
    if (v && !isNaN(parseFloat(v))) { await api.contribute(id, parseFloat(v)); load(); }
  };

  return (
    <div className="space-y-5">
      <h2 className="text-xl font-semibold">Savings goals</h2>
      <form onSubmit={add} className="card flex flex-wrap gap-3 items-end">
        <input className="input w-52" placeholder="Goal (e.g. New laptop)" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
        <input className="input w-40" type="number" min="1" required placeholder="Target ₹" value={f.target_amount} onChange={(e) => setF({ ...f, target_amount: e.target.value })} />
        <input className="input w-44" type="date" value={f.deadline} onChange={(e) => setF({ ...f, deadline: e.target.value })} />
        <button className="btn">Add goal</button>
        {err && <span className="text-sm text-red-600">{err}</span>}
      </form>
      <div className="grid md:grid-cols-2 gap-4">
        {goals.length === 0 && <p className="text-sm text-slate-500">No goals yet.</p>}
        {goals.map((g) => (
          <div key={g.id} className="card space-y-2">
            <div className="flex justify-between"><span className="font-medium">{g.name}</span><span className="text-sm text-slate-500">{g.deadline || "No deadline"}</span></div>
            <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden"><div className="h-full bg-indigo-500" style={{ width: `${g.progress}%` }} /></div>
            <p className="text-sm">{inr(g.saved_amount)} of {inr(g.target_amount)} ({g.progress}%)
              {g.months_left && g.progress < 100 ? ` · ~${inr((g.target_amount - g.saved_amount) / g.months_left)}/month needed` : ""}</p>
            <div className="flex gap-2">
              <button className="btn-ghost" onClick={() => contribute(g.id)}>+ Add savings</button>
              <button className="btn-ghost text-red-600" onClick={async () => { await api.deleteGoal(g.id); load(); }}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";

export default function Auth({ mode }) {
  const [f, setF] = useState({ name: "", email: "", password: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();
  const isReg = mode === "register";

  async function submit(e) {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const r = isReg ? await api.register(f) : await api.login({ email: f.email, password: f.password });
      localStorage.setItem("token", r.access_token);
      nav("/");
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-3">
        <h1 className="text-xl font-bold text-indigo-600">💰 FinSight AI</h1>
        <p className="text-sm text-slate-500">{isReg ? "Create your account" : "Log in to your account"}</p>
        {isReg && <input className="input" placeholder="Name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />}
        <input className="input" type="email" placeholder="Email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />
        <input className="input" type="password" placeholder="Password (min 8 chars)" required minLength={8} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} />
        {err && <p className="text-sm text-red-600">{err}</p>}
        <button className="btn w-full" disabled={busy}>{busy ? "Please wait…" : isReg ? "Sign up" : "Log in"}</button>
        <p className="text-sm text-center text-slate-500">
          {isReg ? <>Have an account? <Link className="text-indigo-600" to="/login">Log in</Link></> : <>New here? <Link className="text-indigo-600" to="/register">Sign up</Link></>}
        </p>
        <p className="text-xs text-slate-400">We never ask for bank credentials. You upload your own statements.</p>
      </form>
    </div>
  );
}

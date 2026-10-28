const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export const CATEGORIES = ["Food","Groceries","Transport","Shopping","Bills","Entertainment","Health","Education","Rent","Travel","Transfers","Other"];
export const inr = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const thisMonth = () => new Date().toISOString().slice(0, 7);

async function req(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = localStorage.getItem("token");
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) payload = form;
  else if (body) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }
  const res = await fetch(BASE + path, { method, headers, body: payload });
  if (res.status === 401 && !path.startsWith("/auth/")) {
    localStorage.removeItem("token");
    window.location.href = "/login";
  }
  if (!res.ok) {
    let msg = "Request failed";
    try { const j = await res.json(); msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return (res.headers.get("content-type") || "").includes("application/json") ? res.json() : res.blob();
}

export const api = {
  register: (b) => req("/auth/register", { method: "POST", body: b }),
  login: (b) => req("/auth/login", { method: "POST", body: b }),
  deleteAccount: () => req("/auth/me", { method: "DELETE" }),
  summary: (m) => req(`/analytics/summary?month=${m}`),
  forecast: () => req("/analytics/forecast"),
  anomalies: () => req("/analytics/anomalies"),
  recs: (m) => req(`/analytics/recommendations?month=${m}`),
  exportFile: (fmt, m) => req(`/analytics/export?format=${fmt}${m ? `&month=${m}` : ""}`),
  listTx: (p) => req("/transactions?" + new URLSearchParams(p)),
  addTx: (b) => req("/transactions", { method: "POST", body: b }),
  updateTx: (id, b) => req(`/transactions/${id}`, { method: "PUT", body: b }),
  deleteTx: (id) => req(`/transactions/${id}`, { method: "DELETE" }),
  importCsv: (file) => { const f = new FormData(); f.append("file", file); return req("/transactions/import", { method: "POST", form: f }); },
  budgets: (m) => req(`/budgets?month=${m}`),
  setBudget: (c, limit) => req(`/budgets/${c}`, { method: "PUT", body: { monthly_limit: limit } }),
  deleteBudget: (c) => req(`/budgets/${c}`, { method: "DELETE" }),
  goals: () => req("/goals"),
  addGoal: (b) => req("/goals", { method: "POST", body: b }),
  contribute: (id, amount) => req(`/goals/${id}/contribute`, { method: "POST", body: { amount } }),
  deleteGoal: (id) => req(`/goals/${id}`, { method: "DELETE" }),
};

export function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

import React from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import Auth from "./pages/Auth.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Transactions from "./pages/Transactions.jsx";
import Budgets from "./pages/Budgets.jsx";
import Goals from "./pages/Goals.jsx";
import Insights from "./pages/Insights.jsx";

const links = [["/", "Dashboard"], ["/transactions", "Transactions"], ["/budgets", "Budgets"], ["/goals", "Goals"], ["/insights", "Insights"]];

function Layout({ children }) {
  const nav = useNavigate();
  const logout = () => { localStorage.removeItem("token"); nav("/login"); };
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center gap-4">
          <span className="font-bold text-indigo-600 text-lg">💰 FinSight AI</span>
          <nav className="flex flex-wrap gap-1 flex-1">
            {links.map(([to, label]) => (
              <NavLink key={to} to={to} end={to === "/"}
                className={({ isActive }) => `px-3 py-1.5 rounded-lg text-sm ${isActive ? "bg-indigo-50 text-indigo-700 font-medium" : "text-slate-600 hover:bg-slate-100"}`}>
                {label}
              </NavLink>
            ))}
          </nav>
          <button className="btn-ghost" onClick={logout}>Log out</button>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
      <footer className="text-center text-xs text-slate-400 pb-6">Insights are informational only and not financial advice.</footer>
    </div>
  );
}

function Private({ children }) {
  return localStorage.getItem("token") ? <Layout>{children}</Layout> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth mode="login" />} />
      <Route path="/register" element={<Auth mode="register" />} />
      <Route path="/" element={<Private><Dashboard /></Private>} />
      <Route path="/transactions" element={<Private><Transactions /></Private>} />
      <Route path="/budgets" element={<Private><Budgets /></Private>} />
      <Route path="/goals" element={<Private><Goals /></Private>} />
      <Route path="/insights" element={<Private><Insights /></Private>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

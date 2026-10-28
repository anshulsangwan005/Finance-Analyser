"""Expense forecasting: weighted moving average + damped linear trend, with a one-step backtest (MAPE)."""
import numpy as np
import pandas as pd


def _predict(vals) -> float:
    v = np.asarray(vals, float)
    n = len(v)
    if n == 1:
        return float(v[0])
    k = min(n, 3)
    wma = np.average(v[-k:], weights=np.arange(1, k + 1))
    if n >= 3:
        slope = np.polyfit(np.arange(n), v, 1)[0]
        wma += 0.5 * slope
    return float(max(wma, 0))


def _band(vals, pred):
    v = np.asarray(vals, float)
    spread = float(v.std()) if len(v) >= 3 else pred * 0.2
    return max(pred - spread, 0.0), pred + spread


def backtest_mape(vals) -> float | None:
    v = list(vals)
    if len(v) < 4:
        return None
    errs = [abs(v[i] - _predict(v[:i])) / max(v[i], 1.0) for i in range(3, len(v))]
    return round(float(np.mean(errs)) * 100, 1)


def forecast(df: pd.DataFrame, today: pd.Timestamp | None = None) -> dict:
    """df: expense rows with columns date (datetime), category, amount."""
    if df.empty:
        return {"available": False, "reason": "Add or import some expenses first."}
    today = today or pd.Timestamp.today()
    cur = today.to_period("M")
    d = df.copy()
    d["month"] = pd.to_datetime(d["date"]).dt.to_period("M")
    full = d[d["month"] < cur]
    if full["month"].nunique() < 1:  # only current month available -> use it, flagged low confidence
        full = d
    months = pd.period_range(full["month"].min(), full["month"].max(), freq="M")
    piv = full.pivot_table(index="month", columns="category", values="amount", aggfunc="sum").reindex(months).fillna(0)
    total = piv.sum(axis=1)
    pred_total = _predict(total.values)
    lo, hi = _band(total.values, pred_total)
    cats = []
    for c in piv.columns:
        p = _predict(piv[c].values)
        l, h = _band(piv[c].values, p)
        cats.append({"category": c, "predicted": round(p, 2), "low": round(l, 2), "high": round(h, 2),
                     "last_month": round(float(piv[c].iloc[-1]), 2)})
    cats.sort(key=lambda x: -x["predicted"])
    return {
        "available": True,
        "next_month": str(cur + 1),
        "months_of_history": int(len(months)),
        "low_confidence": len(months) < 3,
        "total": {"predicted": round(pred_total, 2), "low": round(lo, 2), "high": round(hi, 2),
                  "backtest_mape": backtest_mape(total.values)},
        "categories": cats,
        "history": [{"month": str(m), "total": round(float(v), 2)} for m, v in total.items()],
    }

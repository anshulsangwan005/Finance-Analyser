"""Anomaly + duplicate detection (Isolation Forest + z-score / IQR; duplicate = same merchant+amount within 1 day)."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .categorizer import clean


def find_duplicates(df: pd.DataFrame) -> dict[int, str]:
    out: dict[int, str] = {}
    if df.empty:
        return out
    d = df.copy()
    d["key"] = d["description"].map(clean)
    d["date"] = pd.to_datetime(d["date"])
    for (_, _, _), g in d.sort_values(["date", "id"]).groupby(["key", "amount", "type"]):
        prev = None
        for _, r in g.iterrows():
            if prev is not None and (r["date"] - prev["date"]).days <= 1:
                out[int(r["id"])] = f"Possible duplicate of transaction #{int(prev['id'])}"
            prev = r
    return out


def find_anomalies(df: pd.DataFrame) -> dict[int, str]:
    out: dict[int, str] = {}
    exp = df[df["type"] == "expense"]
    for cat, g in exp.groupby("category"):
        if len(g) < 6:
            continue
        x = np.log1p(g["amount"].values)
        mu, sd = x.mean(), x.std() or 1e-9
        z = (x - mu) / sd
        q1, q3 = np.percentile(g["amount"], [25, 75])
        fence = q3 + 1.5 * (q3 - q1)
        iso_flag = np.zeros(len(g), bool)
        if len(g) >= 20:
            iso_flag = IsolationForest(contamination=0.05, random_state=0).fit_predict(x.reshape(-1, 1)) == -1
        for (_, r), zi, iso in zip(g.iterrows(), z, iso_flag):
            if (zi > 3 or (r["amount"] > fence and zi > 1.5) or (iso and zi > 2)) and r["amount"] > mu:
                typical = float(np.expm1(mu))
                out[int(r["id"])] = f"Unusually high for {cat} (typical ~₹{typical:,.0f})"
    return out


def detect(df: pd.DataFrame) -> tuple[dict[int, str], dict[int, str]]:
    if df.empty:
        return {}, {}
    return find_anomalies(df), find_duplicates(df)

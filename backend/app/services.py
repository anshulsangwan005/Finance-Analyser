from datetime import date

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from .ml import anomaly
from .models import Budget, CategoryRule, Transaction


def tx_df(db: Session, user_id: int) -> pd.DataFrame:
    rows = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    return pd.DataFrame([{"id": r.id, "date": pd.Timestamp(r.date), "description": r.description, "amount": r.amount,
                          "type": r.type, "category": r.category} for r in rows],
                        columns=["id", "date", "description", "amount", "type", "category"])


def user_rules(db: Session, user_id: int) -> dict[str, str]:
    return {r.keyword: r.category for r in db.query(CategoryRule).filter(CategoryRule.user_id == user_id)}


def refresh_flags(db: Session, user_id: int) -> None:
    """Re-run anomaly + duplicate detection over all of a user's transactions."""
    df = tx_df(db, user_id)
    anomalies, dupes = anomaly.detect(df)
    for t in db.query(Transaction).filter(Transaction.user_id == user_id):
        reasons = [x for x in (anomalies.get(t.id), dupes.get(t.id)) if x]
        t.is_anomaly, t.is_duplicate = t.id in anomalies, t.id in dupes
        t.flag_reason = "; ".join(reasons)
    db.commit()


def month_bounds(month: str | None) -> tuple[date, date, str]:
    today = date.today()
    if month:
        y, m = map(int, month.split("-"))
    else:
        y, m = today.year, today.month
    start = date(y, m, 1)
    end = date(y + (m == 12), (m % 12) + 1, 1)
    return start, end, f"{y:04d}-{m:02d}"


def expense_by_category(db: Session, user_id: int, start: date, end: date) -> dict[str, float]:
    rows = (db.query(Transaction.category, func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.type == "expense",
                    Transaction.date >= start, Transaction.date < end)
            .group_by(Transaction.category).all())
    return {c: float(s) for c, s in rows}


def month_income(db: Session, user_id: int, start: date, end: date) -> float:
    s = (db.query(func.sum(Transaction.amount))
         .filter(Transaction.user_id == user_id, Transaction.type == "income",
                 Transaction.date >= start, Transaction.date < end).scalar())
    return float(s or 0)


def budget_status(db: Session, user_id: int, month: str | None) -> list[dict]:
    start, end, _ = month_bounds(month)
    spent = expense_by_category(db, user_id, start, end)
    out = []
    for b in db.query(Budget).filter(Budget.user_id == user_id).order_by(Budget.category):
        s = spent.get(b.category, 0.0)
        pct = s / b.monthly_limit * 100 if b.monthly_limit else 0
        out.append({"category": b.category, "limit": b.monthly_limit, "spent": round(s, 2), "pct": round(pct, 1),
                    "level": "exceeded" if pct >= 100 else "warning" if pct >= 80 else "ok"})
    return out

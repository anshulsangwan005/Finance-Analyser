import csv
import io
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..ml import forecast as fc
from ..ml import recommend
from ..models import Goal, Transaction, User
from ..services import (budget_status, expense_by_category, month_bounds,
                        month_income, refresh_flags, tx_df)
from .goals import _out as goal_out

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(month: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    start, end, label = month_bounds(month)
    by_cat = expense_by_category(db, user.id, start, end)
    income = month_income(db, user.id, start, end)
    expense = sum(by_cat.values())
    df = tx_df(db, user.id)
    trend = []
    if not df.empty:
        df["m"] = df["date"].dt.to_period("M")
        g = df.pivot_table(index="m", columns="type", values="amount", aggfunc="sum").fillna(0).tail(6)
        for m, r in g.iterrows():
            trend.append({"month": str(m), "expense": round(float(r.get("expense", 0)), 2),
                          "income": round(float(r.get("income", 0)), 2)})
    return {"month": label, "income": round(income, 2), "expense": round(expense, 2),
            "savings": round(income - expense, 2),
            "by_category": [{"category": k, "amount": round(v, 2)} for k, v in sorted(by_cat.items(), key=lambda x: -x[1])],
            "trend": trend}


@router.get("/forecast")
def forecast(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    df = tx_df(db, user.id)
    return fc.forecast(df[df["type"] == "expense"])


@router.get("/anomalies")
def anomalies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Transaction).filter(Transaction.user_id == user.id,
                                        (Transaction.is_anomaly == True) | (Transaction.is_duplicate == True)  # noqa: E712
                                        ).order_by(Transaction.date.desc()).all()
    return [{"id": t.id, "date": t.date, "description": t.description, "amount": t.amount, "category": t.category,
             "is_anomaly": t.is_anomaly, "is_duplicate": t.is_duplicate, "reason": t.flag_reason} for t in rows]


@router.post("/rescan")
def rescan(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    refresh_flags(db, user.id)
    return {"ok": True}


@router.get("/recommendations")
def recommendations(month: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    start, end, _ = month_bounds(month)
    df = tx_df(db, user.id)
    f = fc.forecast(df[df["type"] == "expense"])
    goals = [goal_out(g) for g in db.query(Goal).filter(Goal.user_id == user.id)]
    n_flag = db.query(Transaction).filter(Transaction.user_id == user.id, Transaction.date >= start,
                                          Transaction.date < end,
                                          (Transaction.is_anomaly == True) | (Transaction.is_duplicate == True)).count()  # noqa: E712
    recs = recommend.build(expense_by_category(db, user.id, start, end), month_income(db, user.id, start, end),
                           budget_status(db, user.id, month), f, goals, n_flag)
    return {"recommendations": recs,
            "disclaimer": "Informational only. This is not licensed financial, tax or investment advice."}


@router.get("/export")
def export(format: str = "csv", month: str | None = None, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    q = db.query(Transaction).filter(Transaction.user_id == user.id)
    label = "all"
    if month:
        s, e, label = month_bounds(month)
        q = q.filter(Transaction.date >= s, Transaction.date < e)
    rows = q.order_by(Transaction.date).all()
    if format == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["date", "description", "type", "category", "amount"])
        for t in rows:
            w.writerow([t.date, t.description, t.type, t.category, t.amount])
        return Response(buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="transactions_{label}.csv"'})
    if format == "pdf":
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        out = io.BytesIO()
        doc = SimpleDocTemplate(out, pagesize=A4)
        inc = sum(t.amount for t in rows if t.type == "income")
        exp = sum(t.amount for t in rows if t.type == "expense")
        st = getSampleStyleSheet()
        data = [["Date", "Description", "Category", "Amount (INR)"]] + [
            [str(t.date), t.description[:38], t.category, f"{'-' if t.type == 'expense' else '+'}{t.amount:,.2f}"]
            for t in rows]
        tbl = Table(data, repeatRows=1, colWidths=[70, 220, 90, 90])
        tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                                 ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8),
                                 ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("ALIGN", (3, 0), (3, -1), "RIGHT")]))
        doc.build([Paragraph(f"Expense Report ({label})", st["Title"]),
                   Paragraph(f"Income: {inc:,.2f} | Expenses: {exp:,.2f} | Net: {inc - exp:,.2f} INR", st["Normal"]),
                   Spacer(1, 12), tbl])
        return Response(out.getvalue(), media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="report_{label}.pdf"'})
    raise HTTPException(400, "format must be csv or pdf")

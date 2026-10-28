import io
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..config import EXPENSE_CATEGORIES, INCOME_CATEGORY
from ..database import get_db
from ..deps import get_current_user
from ..ml import categorizer
from ..models import CategoryRule, Transaction, User
from ..schemas import TxIn, TxOut, TxUpdate
from ..services import month_bounds, refresh_flags, user_rules

router = APIRouter(prefix="/transactions", tags=["transactions"])
ALL_CATEGORIES = EXPENSE_CATEGORIES + [INCOME_CATEGORY]


@router.get("/categories")
def categories():
    return {"expense": EXPENSE_CATEGORIES, "income": INCOME_CATEGORY}


@router.get("", response_model=list[TxOut])
def list_tx(month: Optional[str] = None, category: Optional[str] = None, q: Optional[str] = None,
            flagged: bool = False, limit: int = Query(200, le=1000), offset: int = 0,
            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    qs = db.query(Transaction).filter(Transaction.user_id == user.id)
    if month:
        s, e, _ = month_bounds(month)
        qs = qs.filter(Transaction.date >= s, Transaction.date < e)
    if category:
        qs = qs.filter(Transaction.category == category)
    if q:
        qs = qs.filter(Transaction.description.ilike(f"%{q}%"))
    if flagged:
        qs = qs.filter((Transaction.is_anomaly == True) | (Transaction.is_duplicate == True))  # noqa: E712
    return qs.order_by(Transaction.date.desc(), Transaction.id.desc()).offset(offset).limit(limit).all()


@router.post("", response_model=TxOut, status_code=201)
def create_tx(data: TxIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.type == "income":
        cat, conf = INCOME_CATEGORY, 1.0
    elif data.category:
        if data.category not in EXPENSE_CATEGORIES:
            raise HTTPException(422, "Unknown category")
        cat, conf = data.category, 1.0
    else:
        cat, conf = categorizer.predict([data.description], user_rules(db, user.id))[0]
    t = Transaction(user_id=user.id, date=data.date, description=data.description.strip(), amount=data.amount,
                    type=data.type, category=cat, confidence=conf, source="manual")
    db.add(t)
    db.commit()
    refresh_flags(db, user.id)
    db.refresh(t)
    return t


@router.put("/{tx_id}", response_model=TxOut)
def update_tx(tx_id: int, data: TxUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == user.id).first()
    if not t:
        raise HTTPException(404, "Not found")
    changes = data.model_dump(exclude_unset=True)
    if "category" in changes and changes["category"] not in ALL_CATEGORIES:
        raise HTTPException(422, "Unknown category")
    for k, v in changes.items():
        setattr(t, k, v)
    if "category" in changes:
        t.confidence = 1.0
        # learn from the correction: remember merchant -> category for this user
        kw = categorizer.merchant_keyword(t.description)
        if kw and t.type == "expense":
            rule = db.query(CategoryRule).filter_by(user_id=user.id, keyword=kw).first()
            if rule:
                rule.category = t.category
            else:
                db.add(CategoryRule(user_id=user.id, keyword=kw, category=t.category))
    db.commit()
    refresh_flags(db, user.id)
    db.refresh(t)
    return t


@router.delete("/{tx_id}", status_code=204)
def delete_tx(tx_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == user.id).first()
    if not t:
        raise HTTPException(404, "Not found")
    db.delete(t)
    db.commit()
    refresh_flags(db, user.id)


# ---------- CSV import (FR3) with flexible column detection (Risk R5) ----------
def _find(cols: list[str], keys: list[str]) -> Optional[str]:
    for k in keys:
        for c in cols:
            if (c == k) if len(k) <= 3 else (k in c):  # short keys (dr/cr) must match exactly
                return c
    return None


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(r"[₹,\s]|INR|Rs\.?", "", regex=True)
                         .str.replace(r"^\((.*)\)$", r"-\1", regex=True), errors="coerce")


def parse_csv(content: bytes) -> tuple[list[dict], int]:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=enc, skipinitialspace=True)
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f"Could not read CSV: {e}")
    df.columns = [str(c).strip().lower() for c in df.columns]
    cols = list(df.columns)
    c_date = _find(cols, ["date"])
    c_desc = _find(cols, ["description", "narration", "details", "particulars", "remarks", "merchant", "payee"])
    c_debit = _find(cols, ["debit", "withdrawal", "dr"])
    c_credit = _find(cols, ["credit", "deposit", "cr"])
    c_amt = _find(cols, ["amount", "amt"])
    c_type = _find(cols, ["type", "dr/cr"])
    if not c_date or not c_desc or not (c_amt or c_debit or c_credit):
        raise HTTPException(400, f"CSV needs date, description and amount (or debit/credit) columns. Found: {cols}")

    df["_date"] = pd.to_datetime(df[c_date], dayfirst=True, errors="coerce")
    rows, skipped = [], 0
    if c_debit or c_credit:
        deb = _num(df[c_debit]).fillna(0) if c_debit else 0
        cred = _num(df[c_credit]).fillna(0) if c_credit else 0
        df["_amt"] = cred - deb  # negative = expense
    else:
        a = _num(df[c_amt])
        if c_type:
            is_exp = df[c_type].astype(str).str.lower().str.contains("debit|dr|expense|withdraw")
            a = a.abs() * is_exp.map({True: -1, False: 1})
        elif (a < 0).any():
            pass  # negative = expense, positive = income
        else:
            a = -a.abs()  # all positive -> treat as expenses
        df["_amt"] = a
    for _, r in df.iterrows():
        if pd.isna(r["_date"]) or pd.isna(r["_amt"]) or r["_amt"] == 0 or pd.isna(r[c_desc]):
            skipped += 1
            continue
        rows.append({"date": r["_date"].date(), "description": str(r[c_desc]).strip()[:500],
                     "amount": abs(float(r["_amt"])), "type": "expense" if r["_amt"] < 0 else "income"})
    return rows, skipped


@router.post("/import")
async def import_csv(file: UploadFile = File(...), user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 5 MB)")
    rows, skipped = parse_csv(content)
    if not rows:
        raise HTTPException(400, "No valid rows found in the CSV")
    exp_idx = [i for i, r in enumerate(rows) if r["type"] == "expense"]
    preds = categorizer.predict([rows[i]["description"] for i in exp_idx], user_rules(db, user.id))
    pmap = dict(zip(exp_idx, preds))
    for i, r in enumerate(rows):
        cat, conf = pmap.get(i, (INCOME_CATEGORY, 1.0))
        db.add(Transaction(user_id=user.id, source="csv", category=cat, confidence=conf, **r))
    db.commit()
    refresh_flags(db, user.id)
    return {"imported": len(rows), "skipped": skipped}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import EXPENSE_CATEGORIES
from ..database import get_db
from ..deps import get_current_user
from ..models import Budget, User
from ..schemas import BudgetIn
from ..services import budget_status

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("")
def list_budgets(month: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return budget_status(db, user.id, month)


@router.put("/{category}")
def set_budget(category: str, data: BudgetIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if category not in EXPENSE_CATEGORIES:
        raise HTTPException(422, "Unknown category")
    b = db.query(Budget).filter_by(user_id=user.id, category=category).first()
    if b:
        b.monthly_limit = data.monthly_limit
    else:
        db.add(Budget(user_id=user.id, category=category, monthly_limit=data.monthly_limit))
    db.commit()
    return {"category": category, "limit": data.monthly_limit}


@router.delete("/{category}", status_code=204)
def delete_budget(category: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Budget).filter_by(user_id=user.id, category=category).delete()
    db.commit()

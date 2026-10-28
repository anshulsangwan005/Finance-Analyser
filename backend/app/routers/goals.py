from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Goal, User
from ..schemas import ContributeIn, GoalIn

router = APIRouter(prefix="/goals", tags=["goals"])


def _out(g: Goal) -> dict:
    months_left = None
    if g.deadline:
        today = date.today()
        months_left = max((g.deadline.year - today.year) * 12 + g.deadline.month - today.month, 1)
    return {"id": g.id, "name": g.name, "target_amount": g.target_amount, "saved_amount": g.saved_amount,
            "deadline": g.deadline, "months_left": months_left,
            "progress": round(min(g.saved_amount / g.target_amount * 100, 100), 1) if g.target_amount else 0}


def _get(db, user, gid) -> Goal:
    g = db.query(Goal).filter(Goal.id == gid, Goal.user_id == user.id).first()
    if not g:
        raise HTTPException(404, "Not found")
    return g


@router.get("")
def list_goals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_out(g) for g in db.query(Goal).filter(Goal.user_id == user.id).order_by(Goal.id)]


@router.post("", status_code=201)
def create_goal(data: GoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = Goal(user_id=user.id, **data.model_dump())
    db.add(g)
    db.commit()
    return _out(g)


@router.post("/{gid}/contribute")
def contribute(gid: int, data: ContributeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = _get(db, user, gid)
    g.saved_amount = max(g.saved_amount + data.amount, 0)
    db.commit()
    return _out(g)


@router.delete("/{gid}", status_code=204)
def delete_goal(gid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_get(db, user, gid))
    db.commit()

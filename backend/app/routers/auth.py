from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email already registered")
    user = User(email=email, name=data.name, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user.id))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenOut(access_token=create_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.delete("/me", status_code=204)
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """DPDP Act: right to erasure. Deletes the user and all of their data."""
    from ..models import Budget, CategoryRule, Goal, Transaction
    for M in (Transaction, Budget, Goal, CategoryRule):
        db.query(M).filter(M.user_id == user.id).delete()
    db.delete(user)
    db.commit()

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    model_config = {"from_attributes": True}


class TxIn(BaseModel):
    date: date
    description: str = Field(min_length=1, max_length=500)
    amount: float = Field(gt=0)
    type: str = Field(pattern="^(expense|income)$")
    category: Optional[str] = None


class TxUpdate(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[str] = Field(default=None, pattern="^(expense|income)$")
    category: Optional[str] = None


class TxOut(BaseModel):
    id: int
    date: date
    description: str
    amount: float
    type: str
    category: str
    confidence: float
    source: str
    is_anomaly: bool
    is_duplicate: bool
    flag_reason: str
    model_config = {"from_attributes": True}


class BudgetIn(BaseModel):
    monthly_limit: float = Field(gt=0)


class GoalIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_amount: float = Field(gt=0)
    saved_amount: float = Field(default=0, ge=0)
    deadline: Optional[date] = None


class ContributeIn(BaseModel):
    amount: float

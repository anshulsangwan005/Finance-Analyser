from datetime import datetime

from sqlalchemy import (Boolean, Column, Date, DateTime, Float, ForeignKey,
                        Integer, String, UniqueConstraint)

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(120), default="")
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)  # always positive
    type = Column(String(10), nullable=False)  # expense | income
    category = Column(String(50), nullable=False, default="Other")
    confidence = Column(Float, default=1.0)
    source = Column(String(10), default="manual")  # manual | csv
    is_anomaly = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    flag_reason = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category", name="uq_budget_user_cat"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category = Column(String(50), nullable=False)
    monthly_limit = Column(Float, nullable=False)


class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(120), nullable=False)
    target_amount = Column(Float, nullable=False)
    saved_amount = Column(Float, default=0.0)
    deadline = Column(Date, nullable=True)


class CategoryRule(Base):
    """User corrections: merchant keyword -> category (feedback loop for the ML model)."""
    __tablename__ = "category_rules"
    __table_args__ = (UniqueConstraint("user_id", "keyword", name="uq_rule_user_kw"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    keyword = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)

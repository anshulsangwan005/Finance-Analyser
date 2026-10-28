import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finance.db")
# Render/Heroku style URLs use postgres:// which SQLAlchemy 2 rejects
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "720"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

EXPENSE_CATEGORIES = [
    "Food", "Groceries", "Transport", "Shopping", "Bills", "Entertainment",
    "Health", "Education", "Rent", "Travel", "Transfers", "Other",
]
INCOME_CATEGORY = "Income"
# 50/30/20 rule mapping
NEEDS = {"Rent", "Bills", "Groceries", "Transport", "Health", "Education"}
WANTS = {"Food", "Shopping", "Entertainment", "Travel", "Transfers", "Other"}

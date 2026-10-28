from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (register tables)
from .config import CORS_ORIGINS
from .database import Base, engine
from .ml import categorizer
from .routers import analytics, auth, budgets, goals, transactions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Personal Finance & Expense Analyzer", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for r in (auth.router, transactions.router, budgets.router, goals.router, analytics.router):
    app.include_router(r)


@app.on_event("startup")
def warm_model():
    categorizer.get_model()  # load (or train once) so the first request is fast


@app.get("/health")
def health():
    return {"status": "ok"}

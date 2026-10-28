# FinSight AI: Personal Finance & Expense Analyzer

Capstone project (Team G427, Bennett University). Web app that imports/enters transactions, auto-categorizes them
with ML, visualizes spending, tracks budgets & goals, forecasts next month's spend, flags anomalies/duplicates,
and gives rule-based savings advice (50/30/20).

| Layer | Tech |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, SQLAlchemy, JWT + bcrypt |
| Database | PostgreSQL (SQLite for local dev) |
| ML | scikit-learn (TF-IDF + Logistic Regression), weighted-MA/trend forecast, Isolation Forest + z-score/IQR |
| Deploy | Docker, Render (API + DB), Vercel (frontend) |

## Project layout
```
backend/   FastAPI app (app/routers, app/ml), train.py, tests/, Dockerfile
frontend/  React app (src/pages), Dockerfile, vercel.json
samples/   sample_statement.csv for testing import
docker-compose.yml   run everything locally
render.yaml          Render blueprint (API + Postgres)
```

## Run locally (no Docker)
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # Windows: copy .env.example .env
python train.py                                         # trains + saves the categorizer
uvicorn app.main:app --reload                           # http://localhost:8000/docs

# Frontend (new terminal)
cd frontend
cp .env.example .env
npm install
npm run dev                                             # http://localhost:5173
```

## Run locally (Docker)
```bash
docker compose up --build
```
Open http://localhost:5173 (API docs at http://localhost:8000/docs).

## Tests
```bash
cd backend && pytest -q
```

## Deploy (free tier): Render + Vercel
See the step-by-step guide in the chat answer, summarized here:
1. Push this repo to GitHub.
2. Render: New > Blueprint > select repo (uses `render.yaml`). Note the API URL.
3. Vercel: Import repo, **Root Directory = `frontend`**, env var `VITE_API_URL=<Render API URL>`.
4. Back on Render, set `CORS_ORIGINS` to your Vercel URL and redeploy.

## Using the app
1. Sign up, then go to **Transactions > Import CSV** and upload `samples/sample_statement.csv`.
2. Check **Dashboard**, set **Budgets**, add **Goals**, and open **Insights** for forecast, flags and advice.

## Notes / honest limitations
- The categorizer is trained on **synthetic** UPI-style data, so the near-100% test F1 is optimistic. Validate on
  real, consented statements before claiming the 85% F1 target. User corrections are stored as per-user rules.
- Forecast uses a lightweight weighted-moving-average + trend model (Prophet/ARIMA can be swapped in `ml/forecast.py`).
- Tables are created automatically on startup (no migrations). Add Alembic if the schema will evolve.
- CSV rule: if the file has an `Amount` column with any negative values, negatives are expenses; if all positive, all are treated as expenses.

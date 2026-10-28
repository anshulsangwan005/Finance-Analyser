import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def auth_headers():
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "password123", "name": "A"})
    if r.status_code == 409:
        r = client.post("/auth/login", json={"email": "a@b.com", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_requires_auth():
    assert client.get("/transactions").status_code == 401


def test_bad_login():
    assert client.post("/auth/login", json={"email": "x@y.com", "password": "nope12345"}).status_code == 401


def test_manual_transaction_is_categorized():
    h = auth_headers()
    r = client.post("/transactions", headers=h,
                    json={"date": "2026-10-01", "description": "UPI/SWIGGY/12345", "amount": 350, "type": "expense"})
    assert r.status_code == 201 and r.json()["category"] == "Food"


def test_correction_creates_rule():
    h = auth_headers()
    t = client.post("/transactions", headers=h, json={"date": "2026-10-02", "description": "CORNER SHOP 99",
                                                     "amount": 120, "type": "expense"}).json()
    client.put(f"/transactions/{t['id']}", headers=h, json={"category": "Groceries"})
    t2 = client.post("/transactions", headers=h, json={"date": "2026-10-03", "description": "CORNER SHOP 55",
                                                      "amount": 80, "type": "expense"}).json()
    assert t2["category"] == "Groceries"


def test_csv_import_and_analytics():
    h = auth_headers()
    csv = "Date,Description,Debit,Credit\n01/09/2026,UPI/ZOMATO/1,250,\n02/09/2026,SALARY,,50000\n03/09/2026,UBER TRIP,180,\n"
    r = client.post("/transactions/import", headers=h, files={"file": ("s.csv", csv, "text/csv")})
    assert r.json()["imported"] == 3
    s = client.get("/analytics/summary?month=2026-09", headers=h).json()
    assert s["income"] == 50000 and s["expense"] == 430
    assert client.get("/analytics/forecast", headers=h).status_code == 200
    assert client.get("/analytics/recommendations", headers=h).status_code == 200


def test_budget_and_export():
    h = auth_headers()
    assert client.put("/budgets/Food", headers=h, json={"monthly_limit": 1000}).status_code == 200
    assert client.get("/budgets?month=2026-09", headers=h).json()[0]["category"] == "Food"
    assert client.get("/analytics/export?format=csv", headers=h).status_code == 200
    assert client.get("/analytics/export?format=pdf", headers=h).headers["content-type"] == "application/pdf"

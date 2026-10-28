"""Rule-based + forecast-informed recommendations (50/30/20 rule, budgets, savings rate, goals)."""
from ..config import NEEDS, WANTS


def build(month_expense_by_cat: dict[str, float], income: float, budget_status: list[dict],
          forecast: dict, goals: list[dict], n_flagged: int) -> list[dict]:
    recs: list[dict] = []
    spent = sum(month_expense_by_cat.values())

    for b in budget_status:
        if b["pct"] >= 100:
            recs.append({"severity": "high", "title": f"{b['category']} budget exceeded",
                         "message": f"You've spent ₹{b['spent']:,.0f} against a ₹{b['limit']:,.0f} limit. Pause non-essential {b['category'].lower()} spending this month."})
        elif b["pct"] >= 80:
            recs.append({"severity": "medium", "title": f"{b['category']} budget at {b['pct']:.0f}%",
                         "message": f"Only ₹{max(b['limit'] - b['spent'], 0):,.0f} left for {b['category']}."})

    if spent > 0:
        top, amt = max(month_expense_by_cat.items(), key=lambda kv: kv[1])
        share = amt / spent * 100
        if share >= 35:
            recs.append({"severity": "medium", "title": f"{top} dominates your spending",
                         "message": f"{top} is {share:.0f}% of this month's expenses. A 10% cut saves about ₹{amt * 0.1:,.0f}."})

    if income > 0:
        needs = sum(v for k, v in month_expense_by_cat.items() if k in NEEDS)
        wants = sum(v for k, v in month_expense_by_cat.items() if k in WANTS)
        savings = income - spent
        n_pct, w_pct, s_pct = needs / income * 100, wants / income * 100, savings / income * 100
        recs.append({"severity": "info", "title": "50/30/20 check",
                     "message": f"Needs {n_pct:.0f}% (target 50), Wants {w_pct:.0f}% (target 30), Savings {s_pct:.0f}% (target 20)."})
        if s_pct < 20:
            recs.append({"severity": "medium" if s_pct >= 0 else "high", "title": "Savings below 20% of income",
                         "message": f"You'd need to save ₹{max(income * 0.2 - savings, 0):,.0f} more this month to hit 20%. Look at your 'Wants' categories first."})
        if forecast.get("available") and forecast["total"]["predicted"] > income:
            recs.append({"severity": "high", "title": "Next month may exceed income",
                         "message": f"Forecast spending ₹{forecast['total']['predicted']:,.0f} is above this month's income ₹{income:,.0f}."})

    if n_flagged:
        recs.append({"severity": "medium", "title": f"{n_flagged} flagged transaction(s)",
                     "message": "Review unusual or duplicate transactions in the Insights tab and delete any errors."})

    for g in goals:
        remaining = g["target_amount"] - g["saved_amount"]
        if remaining > 0 and g.get("months_left"):
            recs.append({"severity": "info", "title": f"Goal: {g['name']}",
                         "message": f"Save about ₹{remaining / g['months_left']:,.0f}/month to reach it by the deadline."})

    if not recs:
        recs.append({"severity": "info", "title": "Looking good", "message": "Add more transactions, budgets and goals to get tailored suggestions."})
    return recs

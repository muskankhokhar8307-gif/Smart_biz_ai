"""Business-data-grounded insights with a local fallback and optional API."""
import json
import os
import urllib.request
import urllib.error

from analytics import business_kpis, category_performance, inventory_dataframe, simple_sales_diagnostics


def build_business_context(db):
    kpis = business_kpis(db)
    diagnostics = simple_sales_diagnostics(db)
    categories = category_performance(db).head(8).to_dict(orient="records")
    inventory = inventory_dataframe(db)
    low_stock = inventory[inventory["needs_restock"]][
        ["product_name", "category", "stock", "reorder_level"]
    ].to_dict(orient="records") if not inventory.empty else []
    return {"kpis": kpis, "monthly_diagnostic": diagnostics,
            "top_categories_by_revenue": categories, "low_stock_products": low_stock}


def local_answer(question, context):
    q = (question or "").strip().lower()
    k = context["kpis"]
    diagnostic = context["monthly_diagnostic"]
    low_stock = context["low_stock_products"]
    cats = context["top_categories_by_revenue"]

    if any(word in q for word in ("restock", "stock", "inventory")):
        if not low_stock:
            return "No products currently meet their configured reorder threshold. This is based on current stock and reorder levels."
        names = ", ".join(f'{p["product_name"]} (stock {p["stock"]}, reorder level {p["reorder_level"]})' for p in low_stock[:10])
        return "Products at or below their reorder threshold: " + names + ". Consider checking recent demand and supplier lead times before ordering."
    if any(word in q for word in ("profitable", "category", "best category")):
        if not cats:
            return "There is not enough completed sales data to compare categories yet."
        best = max(cats, key=lambda c: float(c.get("gross_profit", 0)))
        return (f'The highest gross-profit category in the recorded data is {best["category"]}: '
                f'₹{float(best["gross_profit"]):,.2f} gross profit and ₹{float(best["revenue"]):,.2f} revenue. '
                "This is based on recorded unit costs and completed sales; it does not account for operating expenses by category.")
    if any(word in q for word in ("decrease", "decline", "drop", "sales")):
        if diagnostic.get("status") != "ok":
            return diagnostic.get("message", "There is not enough monthly sales data to compare periods.")
        pct = diagnostic.get("change_percent")
        pct_text = f"{pct:.2f}%" if pct is not None else "not calculable because previous revenue was zero"
        return (f'Revenue {diagnostic["direction"]} from ₹{diagnostic["previous_revenue"]:,.2f} '
                f'in {diagnostic["previous_month"]} to ₹{diagnostic["current_revenue"]:,.2f} '
                f'in {diagnostic["current_month"]} (change: {pct_text}). '
                "This comparison identifies what changed, not why it changed. Check units sold, product availability, pricing, and category mix to investigate causes.")
    if any(word in q for word in ("profit", "revenue", "expense", "business summary", "summary")):
        return (f'Recorded summary: revenue ₹{k["revenue"]:,.2f}; COGS ₹{k["cogs"]:,.2f}; '
                f'gross profit ₹{k["gross_profit"]:,.2f}; expenses ₹{k["expenses"]:,.2f}; '
                f'estimated net profit ₹{k["net_profit_estimate"]:,.2f}; completed sales {k["orders"]}; '
                f'products {k["products"]}; low-stock products {k["low_stock"]}. '
                "The net-profit figure is only as complete as the costs and expenses entered.")
    return ("I can summarize recorded revenue/profit, compare monthly sales, identify products at or below reorder level, "
            "and compare category gross profit. Ask a specific question. " +
            f"Current recorded revenue is ₹{k['revenue']:,.2f}.")


def _api_answer(question, context):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": (
                "You are SmartBiz AI, a cautious business analytics assistant. Answer only from the JSON business context. "
                "Never invent metrics. Distinguish measured facts from hypotheses and do not assert causes without evidence. "
                "Mention limitations where relevant. Currency is INR."
            )},
            {"role": "user", "content": "Business context JSON:\n" + json.dumps(context, default=str) +
             "\n\nQuestion: " + question}
        ]
    }
    req = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
        return "The AI API could not be reached, so a local answer is shown instead. Details: " + str(exc)


def answer_question(db, question, use_api=True):
    context = build_business_context(db)
    if use_api:
        answer = _api_answer(question, context)
        if answer:
            return answer
    return local_answer(question, context)

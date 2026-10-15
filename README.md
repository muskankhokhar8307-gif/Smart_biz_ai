# SmartBiz AI
**Smart Business Intelligence and Decision Support System**

A local-first business management and analytics project built with Python, SQLite, Pandas, NumPy, Matplotlib, Tkinter, and Streamlit.

## Features
- Product, customer, sales, and expense management.
- SQLite database with foreign keys, transactions, validation, and parameterized queries.
- Inventory is reduced when a sale is recorded; cancelling a sale restores stock.
- Revenue, estimated cost of goods sold, operating expenses, gross profit, and estimated net profit.
- CSV import/export and Excel report export.
- Tkinter desktop app and Streamlit web dashboard share the same database and core modules.
- Charts for monthly revenue, category performance, product performance, and expenses.
- AI insights based on real aggregate metrics, with an optional OpenAI-compatible API.
- Transparent next-month baseline forecast with a simple uncertainty range.
- Sample data seeding and unit tests.

## Important business definitions
- **Revenue:** total amount of completed sales, calculated from the sale price recorded at the time of sale.
- **COGS:** quantity multiplied by the product unit cost recorded at the time of sale.
- **Gross profit:** revenue minus COGS.
- **Net profit estimate:** gross profit minus recorded expenses. This is an estimate and depends on accurate product costs and expense records.
- Cancelled sales are excluded from metrics. Cancelling a completed sale restores its quantity to stock.
- This starter system records one product per sale. Multiple products in a single order can be added later as a separate order/line-item model.

## Requirements
- Windows 10/11
- Python 3.11 or 3.12 recommended
- VS Code (optional, recommended)

## Install on Windows
Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run this for the current terminal only:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run the app
Seed demo data (optional):
```powershell
python seed_data.py
```

Launch desktop app:
```powershell
python main.py
```

Launch web dashboard:
```powershell
python -m streamlit run dashboard.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

Both apps use `database/smartbiz.db` by default. Override with `SMARTBIZ_DB_PATH` if required.

## Optional AI API
Copy `.env.example` to `.env`, then set `OPENAI_API_KEY`. Do not commit `.env`. The API feature is optional; local rule-based insights work without it. Configure `OPENAI_BASE_URL` and `OPENAI_MODEL` for an OpenAI-compatible provider. The API uses Python's standard library and does not require an AI SDK.

## Tests
```powershell
python -m unittest discover -s tests -v
```

## Data import
The dashboard includes CSV import for products, customers, and expenses. The expected columns are shown in the dashboard UI. CSV imports validate rows and report failures; they do not silently discard bad rows. Use a backup before importing large datasets.

## Project structure
```text
SmartBiz_AI/
├── main.py
├── dashboard.py
├── gui.py
├── database.py
├── models.py
├── data_processor.py
├── analytics.py
├── visualization.py
├── ai_assistant.py
├── forecasting.py
├── seed_data.py
├── requirements.txt
├── .env.example
├── database/
├── data/
├── reports/
└── tests/
```

## Limitations / next improvements
- Single-user, local SQLite application; not intended as a multi-user hosted production system.
- A sale currently contains one product. For multi-product orders, introduce Orders and OrderItems.
- Forecasting is a transparent baseline, not a trained predictive model. Use at least 6–12 months of good data before interpreting a forecast.
- AI explanations are decision support, not proof of causation.
- No tax, returns, payment gateway, authentication, or accounting compliance workflows are implemented.

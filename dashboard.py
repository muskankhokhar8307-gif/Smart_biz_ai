"""Neon dark Streamlit dashboard for SmartBiz AI."""
from datetime import date, timedelta
from io import BytesIO
import pandas as pd
import streamlit as st

from database import DatabaseManager
from models import Product, Customer, Sale
from analytics import (
    business_kpis, sales_dataframe, expense_dataframe, monthly_sales,
    category_performance, product_performance, inventory_dataframe,
    simple_sales_diagnostics
)
from visualization import monthly_revenue_chart, category_revenue_chart, expense_category_chart
from ai_assistant import answer_question, build_business_context
from forecasting import forecast_next_month
from data_processor import import_products_csv, import_customers_csv

st.set_page_config(page_title="SmartBiz AI | Analytics", page_icon="📊", layout="wide")

# Dark neon dashboard theme inspired by the supplied reference image.
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp {
    background:
      radial-gradient(ellipse at 8% 0%, rgba(0, 194, 255, .13), transparent 32%),
      radial-gradient(ellipse at 95% 8%, rgba(132, 70, 255, .16), transparent 30%),
      linear-gradient(135deg, #050914 0%, #0a1022 55%, #080b18 100%);
    color: #eaf2ff;
}
.block-container {padding-top: 1.35rem; padding-bottom: 2rem; max-width: 1600px;}
[data-testid="stHeader"] {background: rgba(5,9,20,.78);}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1226 0%, #090d1b 100%);
    border-right: 1px solid rgba(88, 158, 255, .24);
}
[data-testid="stSidebar"] * {color: #dce8ff;}
h1, h2, h3 {color: #f2f7ff !important; letter-spacing: .2px;}
p, label, .stCaption {color: #aebed8;}
[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(19,31,59,.96), rgba(11,18,36,.96));
    border: 1px solid rgba(70,148,255,.28);
    padding: 15px 17px;
    border-radius: 14px;
    box-shadow: 0 8px 28px rgba(0,0,0,.18);
}
[data-testid="stMetricLabel"] {color: #9eb5d9 !important;}
[data-testid="stMetricValue"] {color: #f6f9ff !important; font-weight: 750;}
[data-testid="stMetricDelta"] {color: #53e6bb !important;}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(86,145,240,.22) !important;
    background: rgba(11,18,37,.72);
    border-radius: 14px;
}
.stButton > button, .stDownloadButton > button, button[kind="primary"] {
    border: 1px solid rgba(54,199,255,.48);
    color: #f4f8ff;
    background: linear-gradient(100deg, #1165a9, #5b42c8);
    border-radius: 9px;
    font-weight: 650;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #62e7ff;
    color: white;
    box-shadow: 0 0 16px rgba(49,188,255,.22);
}
input, textarea, [data-baseweb="select"] > div {
    background-color: #101a31 !important;
    color: #eef5ff !important;
    border-color: #263b62 !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid rgba(82,145,240,.24);
    border-radius: 10px;
    overflow: hidden;
}
hr {border-color: rgba(99,155,245,.20);}
.sb-hero {
    padding: 23px 26px;
    border-radius: 18px;
    margin-bottom: 18px;
    background:
      radial-gradient(circle at 85% 10%, rgba(111,69,255,.24), transparent 27%),
      linear-gradient(115deg, rgba(14,36,69,.98), rgba(15,20,47,.97));
    border: 1px solid rgba(75,174,255,.35);
    box-shadow: 0 12px 40px rgba(0,0,0,.22);
}
.sb-eyebrow {color:#63ddff; text-transform:uppercase; letter-spacing:2px; font-size:.76rem; font-weight:800;}
.sb-title {font-size:2.1rem; font-weight:850; color:#f4f8ff; line-height:1.18; margin:.25rem 0;}
.sb-subtitle {color:#aabddd; font-size:.95rem;}
.sb-panel {
    padding: 15px 18px;
    border-radius: 13px;
    border: 1px solid rgba(75,147,245,.24);
    background: linear-gradient(145deg, rgba(15,26,50,.95), rgba(10,16,32,.95));
    min-height: 100px;
}
.sb-panel-label {font-size:.8rem; color:#9eb4d6; margin-bottom:7px;}
.sb-panel-value {font-size:1.35rem; font-weight:800; color:#f5f8ff;}
.sb-panel-note {font-size:.78rem; color:#51dfc1; margin-top:5px;}
.sb-insight {
    padding: 13px 15px; border-radius: 11px; margin: 7px 0;
    background: rgba(18,31,57,.88); border-left: 3px solid #43d7ff;
    color: #dbe9ff;
}
.sb-muted {color:#8fa5c9; font-size:.84rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()
today = date.today()
default_start = today - timedelta(days=180)

st.sidebar.markdown("## ◈ SMARTBIZ AI")
st.sidebar.caption("BUSINESS INTELLIGENCE")
page = st.sidebar.radio(
    "WORKSPACE",
    ["Overview", "Products & Inventory", "Customers", "Sales", "Expenses",
     "Data Import", "AI Insights", "Forecasting", "Reports"],
    label_visibility="visible"
)
st.sidebar.divider()
st.sidebar.markdown("### Date range")
start = st.sidebar.date_input("From", value=default_start)
end = st.sidebar.date_input("To", value=today)
st.sidebar.caption("Dashboard metrics use completed sales only.")
if start > end:
    st.sidebar.error("Start date must be on or before end date.")
    st.stop()
start_s, end_s = start.isoformat(), end.isoformat()

def money(v):
    return f"₹{float(v):,.2f}"

def show_df(df):
    st.dataframe(df, use_container_width=True, hide_index=True)

def download_excel(sheets):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()

def hero(title, subtitle, eyebrow="SMART BUSINESS INTELLIGENCE"):
    st.markdown(
        f'<div class="sb-hero"><div class="sb-eyebrow">{eyebrow}</div>'
        f'<div class="sb-title">{title}</div><div class="sb-subtitle">{subtitle}</div></div>',
        unsafe_allow_html=True
    )

def panel(label, value, note=""):
    note_html = f'<div class="sb-panel-note">{note}</div>' if note else ""
    st.markdown(
        f'<div class="sb-panel"><div class="sb-panel-label">{label}</div>'
        f'<div class="sb-panel-value">{value}</div>{note_html}</div>',
        unsafe_allow_html=True
    )

def chart_dark(fig):
    fig.patch.set_facecolor("#0c1428")
    for ax in fig.axes:
        ax.set_facecolor("#0c1428")
        ax.tick_params(colors="#a9bbd9")
        ax.xaxis.label.set_color("#a9bbd9")
        ax.yaxis.label.set_color("#a9bbd9")
        ax.title.set_color("#eef5ff")
        for spine in ax.spines.values():
            spine.set_color("#25395c")
        ax.grid(True, color="#233653", alpha=.55)
    st.pyplot(fig, clear_figure=True, use_container_width=True)

if page == "Overview":
    k = business_kpis(db, start_s, end_s)
    monthly = monthly_sales(db, start_s, end_s)
    categories = category_performance(db, start_s, end_s)
    products = product_performance(db, start_s, end_s)
    expenses = expense_dataframe(db, start_s, end_s)
    diagnostics = simple_sales_diagnostics(db)
    context = build_business_context(db)

    hero("Analytics Dashboard", "Live business performance, inventory signals and decision support in one workspace.")

    top = st.columns(4)
    with top[0]: panel("TOTAL REVENUE", money(k["revenue"]), f'{k["orders"]:,} completed sales')
    with top[1]: panel("GROSS PROFIT", money(k["gross_profit"]), "Revenue minus recorded product cost")
    with top[2]: panel("EST. NET PROFIT", money(k["net_profit_estimate"]), "After recorded expenses")
    with top[3]: panel("INVENTORY ALERTS", str(k["low_stock"]), "Products at/below reorder level")

    st.write("")
    left, right = st.columns([1.8, 1])
    with left:
        st.markdown("### ✦ Revenue Growth")
        if monthly.empty:
            st.info("No sales in the selected date range. Add sales or seed demo data to populate charts.")
        else:
            chart_dark(monthly_revenue_chart(monthly))
    with right:
        st.markdown("### ◉ Business Snapshot")
        c1, c2 = st.columns(2)
        with c1: panel("PRODUCTS", f'{k["products"]:,}', "In catalogue")
        with c2: panel("CUSTOMERS", f'{k["customers"]:,}', "Registered customers")
        c3, c4 = st.columns(2)
        with c3: panel("UNITS SOLD", f'{k["units_sold"]:,}', "Selected period")
        with c4: panel("EXPENSES", money(k["expenses"]), "Selected period")
        if diagnostics.get("status") == "ok":
            direction = "↑" if diagnostics["change"] > 0 else "↓" if diagnostics["change"] < 0 else "→"
            st.markdown(
                f'<div class="sb-insight"><b>Monthly revenue check</b><br>{direction} '
                f'{diagnostics["direction"].title()} by {money(abs(diagnostics["change"]))} '
                f'from {diagnostics["previous_month"]} to {diagnostics["current_month"]}. '
                'This is a comparison, not proof of cause.</div>', unsafe_allow_html=True
            )
        else:
            st.markdown(f'<div class="sb-insight">{diagnostics.get("message", "More sales history is needed for a monthly comparison.")}</div>', unsafe_allow_html=True)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### ▥ Category Performance")
        if categories.empty: st.info("Category data will appear after sales are recorded.")
        else: chart_dark(category_revenue_chart(categories))
    with col_b:
        st.markdown("### ◌ AI Insights")
        low = context["low_stock_products"]
        if low:
            names = ", ".join(x["product_name"] for x in low[:4])
            st.markdown(f'<div class="sb-insight">⚠ <b>Restock review</b><br>{names}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="sb-insight">✓ No items are currently at or below their reorder level.</div>', unsafe_allow_html=True)
        if not categories.empty:
            best = categories.sort_values("gross_profit", ascending=False).iloc[0]
            st.markdown(
                f'<div class="sb-insight">✦ <b>Gross-profit leader</b><br>{best["category"]}: '
                f'{money(best["gross_profit"])} gross profit from recorded sales.</div>', unsafe_allow_html=True
            )
        st.markdown('<div class="sb-muted">Insights summarize recorded data; they do not prove why a metric changed.</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### ▤ Recent Sales")
    recent = sales_dataframe(db, start_s, end_s).head(8)
    if recent.empty: st.info("No completed sales found for this date range.")
    else: show_df(recent[["sale_date", "product_name", "category", "customer_name", "quantity", "revenue", "gross_profit"]])

elif page == "Products & Inventory":
    hero("Products & Inventory", "Manage the catalogue, unit costs and reorder thresholds.", "OPERATIONS")
    with st.form("add_product_form", clear_on_submit=True):
        a, b, c = st.columns(3)
        name = a.text_input("Product name")
        category = b.text_input("Category")
        price = c.number_input("Selling price (₹)", min_value=0.0, step=10.0)
        d, e, f = st.columns(3)
        cost = d.number_input("Unit cost (₹)", min_value=0.0, step=10.0)
        stock = e.number_input("Opening stock", min_value=0, step=1)
        reorder = f.number_input("Reorder level", min_value=0, value=5, step=1)
        if st.form_submit_button("＋ Add product"):
            try:
                db.add_product(Product(name, category, price, cost, int(stock), int(reorder)))
                st.success("Product added."); st.rerun()
            except Exception as exc: st.error(str(exc))
    inv = inventory_dataframe(db)
    if not inv.empty:
        low = inv[inv["needs_restock"]]
        if not low.empty: st.warning(f"{len(low)} product(s) at or below reorder level.")
        show_df(inv)
        with st.expander("Delete a product"):
            chosen = st.selectbox("Product", db.list_products(), format_func=lambda p: f'{p["product_id"]} — {p["product_name"]}')
            if st.button("Delete selected product"):
                try: db.delete_product(chosen["product_id"]); st.success("Deleted."); st.rerun()
                except Exception as exc: st.error(str(exc))

elif page == "Customers":
    hero("Customer Directory", "Maintain customer records used for sales tracking.", "CUSTOMER MANAGEMENT")
    with st.form("add_customer_form", clear_on_submit=True):
        a, b, c = st.columns(3)
        name = a.text_input("Customer name")
        city = b.text_input("City")
        email = c.text_input("Email (optional)")
        if st.form_submit_button("＋ Add customer"):
            try: db.add_customer(Customer(name, city, email)); st.success("Customer added."); st.rerun()
            except Exception as exc: st.error(str(exc))
    customers = db.list_customers()
    show_df(pd.DataFrame(customers))
    if customers:
        with st.expander("Delete a customer"):
            chosen = st.selectbox("Customer", customers, format_func=lambda c: f'{c["customer_id"]} — {c["name"]}')
            if st.button("Delete selected customer"):
                try: db.delete_customer(chosen["customer_id"]); st.success("Deleted."); st.rerun()
                except Exception as exc: st.error(str(exc))

elif page == "Sales":
    hero("Sales Management", "Record transactions and keep inventory synchronized.", "REVENUE OPERATIONS")
    products, customers = db.list_products(), db.list_customers()
    if not products or not customers:
        st.info("Add at least one product and one customer before recording a sale.")
    else:
        with st.form("sale_form", clear_on_submit=True):
            a, b, c = st.columns([2, 2, 1])
            product = a.selectbox("Product", products, format_func=lambda x: f'{x["product_id"]} — {x["product_name"]} (stock {x["stock"]})')
            customer = b.selectbox("Customer", customers, format_func=lambda x: f'{x["customer_id"]} — {x["name"]}')
            quantity = c.number_input("Quantity", min_value=1, value=1, step=1)
            sale_date = st.date_input("Sale date", value=today)
            if st.form_submit_button("Record sale"):
                try: db.add_sale(Sale(product["product_id"], customer["customer_id"], int(quantity), sale_date.isoformat())); st.success("Sale recorded; stock reduced."); st.rerun()
                except Exception as exc: st.error(str(exc))
    sales = db.list_sales(start_s, end_s)
    show_df(pd.DataFrame(sales))
    active = [s for s in sales if s["status"] == "completed"]
    if active:
        with st.expander("Cancel a completed sale"):
            chosen = st.selectbox("Sale", active, format_func=lambda s: f'#{s["sale_id"]} {s["sale_date"]} — {s["product_name"]} × {s["quantity"]}')
            if st.button("Cancel sale and restore stock"):
                try: db.cancel_sale(chosen["sale_id"]); st.success("Sale cancelled and stock restored."); st.rerun()
                except Exception as exc: st.error(str(exc))

elif page == "Expenses":
    hero("Expenses", "Record operating costs used in estimated net-profit calculations.", "FINANCIAL TRACKING")
    with st.form("expense_form", clear_on_submit=True):
        a, b, c = st.columns(3)
        category = a.text_input("Expense category")
        amount = b.number_input("Amount (₹)", min_value=0.0, step=100.0)
        expense_date = c.date_input("Expense date", value=today)
        description = st.text_input("Description")
        if st.form_submit_button("＋ Add expense"):
            try: db.add_expense(category, amount, expense_date.isoformat(), description); st.success("Expense recorded."); st.rerun()
            except Exception as exc: st.error(str(exc))
    expenses = expense_dataframe(db, start_s, end_s)
    show_df(expenses)
    if not expenses.empty: chart_dark(expense_category_chart(expenses))

elif page == "Data Import":
    hero("Data Import", "Import validated CSV records. Existing records are not automatically overwritten.", "DATA MANAGEMENT")
    st.warning("Review your file and keep a backup before importing. Failed rows are reported.")
    pf = st.file_uploader("Products CSV: product_name, category, price, unit_cost, stock; optional reorder_level", type=["csv"], key="products_csv")
    if pf and st.button("Import products"):
        path = "data/_uploaded_products.csv"
        with open(path, "wb") as f: f.write(pf.getvalue())
        try:
            result = import_products_csv(db, path)
            st.success(f'Imported {result["imported"]} product(s).')
            if result["errors"]: st.error("\n".join(result["errors"]))
        except Exception as exc: st.error(str(exc))
    cf = st.file_uploader("Customers CSV: name; optional city, email", type=["csv"], key="customers_csv")
    if cf and st.button("Import customers"):
        path = "data/_uploaded_customers.csv"
        with open(path, "wb") as f: f.write(cf.getvalue())
        try:
            result = import_customers_csv(db, path)
            st.success(f'Imported {result["imported"]} customer(s).')
            if result["errors"]: st.error("\n".join(result["errors"]))
        except Exception as exc: st.error(str(exc))

elif page == "AI Insights":
    hero("AI Insights", "Ask questions answered from your actual business records.", "DECISION SUPPORT")
    st.markdown('<div class="sb-insight">The assistant distinguishes measured metrics from hypotheses. It will not claim a cause for a sales change without evidence.</div>', unsafe_allow_html=True)
    question = st.text_area("Ask SmartBiz AI", placeholder="Why did sales decrease? Which products should I restock? Which category has the highest gross profit?")
    use_api = st.checkbox("Use configured optional AI API", value=True)
    if st.button("Analyze business data", type="primary"):
        if not question.strip(): st.warning("Enter a question first.")
        else:
            with st.spinner("Analyzing recorded business metrics..."):
                st.write(answer_question(db, question, use_api=use_api))

elif page == "Forecasting":
    hero("Predictive Trends", "A transparent baseline estimate from historical monthly revenue.", "FORECASTING")
    result = forecast_next_month(db)
    if result["status"] != "ok":
        st.info(result["message"])
    else:
        a, b, c = st.columns(3)
        a.metric(f'Forecast · {result["forecast_month"]}', money(result["prediction"]))
        b.metric("Lower descriptive estimate", money(result["lower"]))
        c.metric("Upper descriptive estimate", money(result["upper"]))
        st.markdown(f'<div class="sb-insight"><b>Method:</b> {result["method"]}<br>{result["message"]}</div>', unsafe_allow_html=True)
        monthly = monthly_sales(db)
        chart_dark(monthly_revenue_chart(monthly))

elif page == "Reports":
    hero("Reports & Exports", "Download filtered sales, expenses, inventory and analysis.", "REPORTING")
    k = business_kpis(db, start_s, end_s)
    sales = sales_dataframe(db, start_s, end_s)
    expenses = expense_dataframe(db, start_s, end_s)
    inventory = inventory_dataframe(db)
    st.markdown("### Selected-period KPIs")
    show_df(pd.DataFrame([k]))
    st.download_button("↓ Download sales CSV", data=sales.to_csv(index=False).encode("utf-8-sig"),
                       file_name="smartbiz_sales.csv", mime="text/csv")
    st.download_button("↓ Download expenses CSV", data=expenses.to_csv(index=False).encode("utf-8-sig"),
                       file_name="smartbiz_expenses.csv", mime="text/csv")
    st.download_button("↓ Download Excel workbook", data=download_excel({
        "KPI Summary": pd.DataFrame([k]), "Sales": sales, "Expenses": expenses,
        "Products": pd.DataFrame(db.list_products()), "Inventory": inventory,
        "Monthly Sales": monthly_sales(db, start_s, end_s),
        "Categories": category_performance(db, start_s, end_s),
        "Products Performance": product_performance(db, start_s, end_s)
    }), file_name="smartbiz_report.xlsx",
       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

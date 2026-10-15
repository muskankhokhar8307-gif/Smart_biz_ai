"""Tkinter desktop UI for core SmartBiz AI workflows."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import logging

from database import DatabaseManager
from models import Product, Customer, Sale
from analytics import business_kpis, monthly_sales, category_performance
from visualization import monthly_revenue_chart, category_revenue_chart

logging.basicConfig(level=logging.INFO)


class SmartBizDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartBiz AI — Business Intelligence")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.db = DatabaseManager()
        self._style()
        self._build()
        self.refresh_all()

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("KPI.TLabel", font=("Segoe UI", 12, "bold"), padding=8)

    def _build(self):
        header = ttk.Frame(self.root, padding=14)
        header.pack(fill="x")
        ttk.Label(header, text="SMARTBIZ AI", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="Business Intelligence & Decision Support").pack(side="left", padx=18)
        ttk.Button(header, text="Refresh", command=self.refresh_all).pack(side="right")

        self.kpi_frame = ttk.Frame(self.root, padding=(12, 0))
        self.kpi_frame.pack(fill="x")
        self.kpi_labels = {}
        for key, label in [("revenue", "Revenue"), ("orders", "Completed Sales"),
                           ("gross_profit", "Gross Profit"), ("net_profit_estimate", "Est. Net Profit"),
                           ("low_stock", "Low Stock")]:
            frame = ttk.LabelFrame(self.kpi_frame, text=label, padding=8)
            frame.pack(side="left", fill="x", expand=True, padx=4, pady=4)
            var = tk.StringVar(value="—")
            ttk.Label(frame, textvariable=var, style="KPI.TLabel").pack()
            self.kpi_labels[key] = var

        tabs = ttk.Notebook(self.root)
        tabs.pack(fill="both", expand=True, padx=12, pady=10)
        self.products_tab = ttk.Frame(tabs, padding=10)
        self.customers_tab = ttk.Frame(tabs, padding=10)
        self.sales_tab = ttk.Frame(tabs, padding=10)
        self.expenses_tab = ttk.Frame(tabs, padding=10)
        self.analytics_tab = ttk.Frame(tabs, padding=10)
        tabs.add(self.products_tab, text="Products")
        tabs.add(self.customers_tab, text="Customers")
        tabs.add(self.sales_tab, text="Record Sale")
        tabs.add(self.expenses_tab, text="Expenses")
        tabs.add(self.analytics_tab, text="Analytics")
        self._build_products()
        self._build_customers()
        self._build_sales()
        self._build_expenses()
        self._build_analytics()

    def _tree(self, parent, columns, headings):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        for col, heading in zip(columns, headings):
            tree.heading(col, text=heading)
            tree.column(col, width=120, anchor="w")
        tree.pack(fill="both", expand=True, pady=8)
        return tree

    def _build_products(self):
        form = ttk.LabelFrame(self.products_tab, text="Add Product", padding=8)
        form.pack(fill="x")
        self.pv = {}
        fields = [("name", "Name"), ("category", "Category"), ("price", "Selling price"),
                  ("cost", "Unit cost"), ("stock", "Opening stock"), ("reorder", "Reorder level")]
        for i, (key, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w", padx=4)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=15).grid(row=1, column=i, padx=4, pady=4)
            self.pv[key] = var
        ttk.Button(form, text="Add Product", command=self.add_product).grid(row=1, column=6, padx=6)
        ttk.Button(form, text="Delete Selected", command=self.delete_product).grid(row=1, column=7, padx=6)
        self.product_tree = self._tree(self.products_tab,
            ("id", "name", "category", "price", "cost", "stock", "reorder"),
            ("ID", "Product", "Category", "Price ₹", "Cost ₹", "Stock", "Reorder"))

    def _build_customers(self):
        form = ttk.LabelFrame(self.customers_tab, text="Add Customer", padding=8)
        form.pack(fill="x")
        self.cv = {}
        for i, (key, label) in enumerate([("name", "Name"), ("city", "City"), ("email", "Email")]):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w", padx=4)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=26).grid(row=1, column=i, padx=4, pady=4)
            self.cv[key] = var
        ttk.Button(form, text="Add Customer", command=self.add_customer).grid(row=1, column=3, padx=8)
        ttk.Button(form, text="Delete Selected", command=self.delete_customer).grid(row=1, column=4, padx=8)
        self.customer_tree = self._tree(self.customers_tab,
            ("id", "name", "city", "email"), ("ID", "Name", "City", "Email"))

    def _build_sales(self):
        form = ttk.LabelFrame(self.sales_tab, text="Record Sale", padding=10)
        form.pack(fill="x")
        products = self.db.list_products()
        customers = self.db.list_customers()
        self.sale_product = tk.StringVar()
        self.sale_customer = tk.StringVar()
        self.sale_qty = tk.StringVar(value="1")
        self.sale_date = tk.StringVar(value=date.today().isoformat())
        ttk.Label(form, text="Product").grid(row=0, column=0, sticky="w")
        self.product_combo = ttk.Combobox(form, textvariable=self.sale_product, state="readonly", width=32)
        self.product_combo.grid(row=1, column=0, padx=4, pady=4)
        ttk.Label(form, text="Customer").grid(row=0, column=1, sticky="w")
        self.customer_combo = ttk.Combobox(form, textvariable=self.sale_customer, state="readonly", width=32)
        self.customer_combo.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(form, text="Quantity").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.sale_qty, width=10).grid(row=1, column=2, padx=4)
        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=0, column=3, sticky="w")
        ttk.Entry(form, textvariable=self.sale_date, width=14).grid(row=1, column=3, padx=4)
        ttk.Button(form, text="Save Sale", command=self.add_sale).grid(row=1, column=4, padx=8)
        ttk.Button(form, text="Cancel Selected Sale", command=self.cancel_sale).grid(row=1, column=5, padx=8)
        self.sales_tree = self._tree(self.sales_tab,
            ("id", "date", "product", "customer", "qty", "amount", "status"),
            ("Sale ID", "Date", "Product", "Customer", "Qty", "Amount ₹", "Status"))

    def _build_expenses(self):
        form = ttk.LabelFrame(self.expenses_tab, text="Add Expense", padding=8)
        form.pack(fill="x")
        self.ev = {}
        fields = [("category", "Category"), ("amount", "Amount ₹"), ("date", "Date YYYY-MM-DD"), ("description", "Description")]
        for i, (key, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w", padx=4)
            var = tk.StringVar(value=date.today().isoformat() if key == "date" else "")
            ttk.Entry(form, textvariable=var, width=24).grid(row=1, column=i, padx=4, pady=4)
            self.ev[key] = var
        ttk.Button(form, text="Add Expense", command=self.add_expense).grid(row=1, column=4, padx=8)
        self.expense_tree = self._tree(self.expenses_tab,
            ("id", "date", "category", "description", "amount"),
            ("ID", "Date", "Category", "Description", "Amount ₹"))

    def _build_analytics(self):
        ttk.Label(self.analytics_tab, text="Use the Streamlit dashboard for interactive charts and exports.").pack(anchor="w")
        self.analytics_text = tk.Text(self.analytics_tab, height=12, wrap="word")
        self.analytics_text.pack(fill="both", expand=True, pady=8)
        ttk.Button(self.analytics_tab, text="Refresh Analytics Summary", command=self.refresh_all).pack(anchor="w")

    def _selected_id(self, tree):
        selected = tree.selection()
        if not selected:
            return None
        return int(tree.item(selected[0], "values")[0])

    def add_product(self):
        try:
            product = Product(self.pv["name"].get(), self.pv["category"].get(),
                              self.pv["price"].get(), self.pv["cost"].get(),
                              int(self.pv["stock"].get()), int(self.pv["reorder"].get() or 5))
            self.db.add_product(product)
            for var in self.pv.values(): var.set("")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Cannot add product", str(exc))

    def delete_product(self):
        pid = self._selected_id(self.product_tree)
        if pid is None: return messagebox.showinfo("Select product", "Select a product first.")
        if messagebox.askyesno("Confirm deletion", "Delete selected product? Products with sales history cannot be deleted."):
            try: self.db.delete_product(pid); self.refresh_all()
            except Exception as exc: messagebox.showerror("Delete failed", str(exc))

    def add_customer(self):
        try:
            self.db.add_customer(Customer(self.cv["name"].get(), self.cv["city"].get(), self.cv["email"].get()))
            for var in self.cv.values(): var.set("")
            self.refresh_all()
        except Exception as exc: messagebox.showerror("Cannot add customer", str(exc))

    def delete_customer(self):
        cid = self._selected_id(self.customer_tree)
        if cid is None: return messagebox.showinfo("Select customer", "Select a customer first.")
        if messagebox.askyesno("Confirm deletion", "Delete selected customer? Customers with sales history cannot be deleted."):
            try: self.db.delete_customer(cid); self.refresh_all()
            except Exception as exc: messagebox.showerror("Delete failed", str(exc))

    def add_sale(self):
        try:
            pmap = {x.split(" — ", 1)[0]: int(x.split(" — ", 1)[0]) for x in self.product_combo["values"]}
            cmap = {x.split(" — ", 1)[0]: int(x.split(" — ", 1)[0]) for x in self.customer_combo["values"]}
            pid = pmap[self.sale_product.get().split(" — ", 1)[0]]
            cid = cmap[self.sale_customer.get().split(" — ", 1)[0]]
            self.db.add_sale(Sale(pid, cid, int(self.sale_qty.get()), self.sale_date.get()))
            self.refresh_all()
            messagebox.showinfo("Sale recorded", "Sale saved and inventory updated.")
        except Exception as exc: messagebox.showerror("Cannot record sale", str(exc))

    def cancel_sale(self):
        sid = self._selected_id(self.sales_tree)
        if sid is None: return messagebox.showinfo("Select sale", "Select a sale first.")
        if messagebox.askyesno("Cancel sale", "Cancel selected sale and restore its stock?"):
            try: self.db.cancel_sale(sid); self.refresh_all()
            except Exception as exc: messagebox.showerror("Cannot cancel sale", str(exc))

    def add_expense(self):
        try:
            self.db.add_expense(self.ev["category"].get(), self.ev["amount"].get(),
                                self.ev["date"].get(), self.ev["description"].get())
            self.ev["category"].set(""); self.ev["amount"].set(""); self.ev["description"].set("")
            self.refresh_all()
        except Exception as exc: messagebox.showerror("Cannot add expense", str(exc))

    def refresh_all(self):
        try:
            k = business_kpis(self.db)
            for key, var in self.kpi_labels.items():
                value = f'₹{k[key]:,.2f}' if key in ("revenue", "gross_profit", "net_profit_estimate") else str(k[key])
                var.set(value)
            self._fill_tree(self.product_tree, [
                (p["product_id"], p["product_name"], p["category"], p["price"], p["unit_cost"], p["stock"], p["reorder_level"])
                for p in self.db.list_products()])
            self._fill_tree(self.customer_tree, [
                (c["customer_id"], c["name"], c["city"], c["email"]) for c in self.db.list_customers()])
            self._fill_tree(self.sales_tree, [
                (s["sale_id"], s["sale_date"], s["product_name"], s["customer_name"], s["quantity"],
                 s["total_amount"], s["status"]) for s in self.db.list_sales()])
            self._fill_tree(self.expense_tree, [
                (e["expense_id"], e["expense_date"], e["category"], e["description"], e["amount"])
                for e in self.db.list_expenses()])
            self.product_combo["values"] = [f'{p["product_id"]} — {p["product_name"]} (stock {p["stock"]})'
                                             for p in self.db.list_products()]
            self.customer_combo["values"] = [f'{c["customer_id"]} — {c["name"]}' for c in self.db.list_customers()]
            self.analytics_text.delete("1.0", "end")
            self.analytics_text.insert("end", "Business summary\n\n")
            for key, value in k.items(): self.analytics_text.insert("end", f"{key.replace('_', ' ').title()}: {value}\n")
            self.analytics_text.insert("end", "\nMetrics use completed sales only. Estimated net profit = revenue - recorded product costs - recorded expenses.\n")
        except Exception as exc:
            logging.exception("Refresh failed")
            messagebox.showerror("Refresh failed", str(exc))

    @staticmethod
    def _fill_tree(tree, rows):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", values=row)


def run_desktop():
    root = tk.Tk()
    SmartBizDesktop(root)
    root.mainloop()

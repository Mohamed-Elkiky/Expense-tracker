# app.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import services
from db import init_db

COLORS = {
    "bg":           "#f5f5f2",
    "surface":      "#ffffff",
    "border":       "#e0ddd4",
    "accent":       "#5349b7",
    "accent_light": "#eeedfe",
    "danger":       "#e24b4a",
    "text":         "#2c2c2a",
    "muted":        "#888780",
}


class ExpenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("820x600")
        self.minsize(700, 500)
        self.configure(bg=COLORS["bg"])
        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------ helpers

    def _card(self, parent) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

    def _label(self, parent, text, size=13, color=None, bold=False, **kw) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=("Helvetica", size, "bold" if bold else "normal"),
            fg=color or COLORS["text"],
            bg=parent.cget("bg"),
            **kw,
        )

    # ------------------------------------------------------------------ build UI

    def _build_ui(self):
        left = tk.Frame(self, bg=COLORS["bg"], width=250)
        left.pack(side="left", fill="y", padx=(16, 8), pady=16)
        left.pack_propagate(False)

        right = tk.Frame(self, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(8, 16), pady=16)

        self._build_form(left)
        self._build_summary(left)
        self._build_table(right)

    def _build_form(self, parent):
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 10))

        inner = tk.Frame(card, bg=COLORS["surface"], padx=14, pady=14)
        inner.pack(fill="both")

        self._label(inner, "Add expense", size=14, bold=True).pack(anchor="w", pady=(0, 12))

        self._label(inner, "Amount (£)", size=12, color=COLORS["muted"]).pack(anchor="w")
        self.amount_var = tk.StringVar()
        tk.Entry(
            inner, textvariable=self.amount_var, font=("Helvetica", 13),
            relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, bd=0
        ).pack(fill="x", ipady=6, pady=(2, 8))

        self._label(inner, "Category", size=12, color=COLORS["muted"]).pack(anchor="w")
        self.cat_var = tk.StringVar(value=services.CATEGORIES[0])
        ttk.Combobox(
            inner, textvariable=self.cat_var,
            values=services.CATEGORIES, state="readonly", font=("Helvetica", 12)
        ).pack(fill="x", pady=(2, 8))

        self._label(inner, "Description", size=12, color=COLORS["muted"]).pack(anchor="w")
        self.desc_var = tk.StringVar()
        tk.Entry(
            inner, textvariable=self.desc_var, font=("Helvetica", 13),
            relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, bd=0
        ).pack(fill="x", ipady=6, pady=(2, 8))

        self._label(inner, "Date (YYYY-MM-DD)", size=12, color=COLORS["muted"]).pack(anchor="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        tk.Entry(
            inner, textvariable=self.date_var, font=("Helvetica", 13),
            relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, bd=0
        ).pack(fill="x", ipady=6, pady=(2, 12))

        tk.Button(
            inner, text="Add expense", command=self._on_add,
            font=("Helvetica", 13, "bold"), fg=COLORS["surface"], bg=COLORS["accent"],
            activebackground="#3c3489", activeforeground=COLORS["surface"],
            relief="flat", cursor="hand2", padx=8, pady=8,
        ).pack(fill="x")

    def _build_summary(self, parent):
        card = self._card(parent)
        card.pack(fill="x")

        inner = tk.Frame(card, bg=COLORS["surface"], padx=14, pady=14)
        inner.pack(fill="both")

        self._label(inner, "This month", size=14, bold=True).pack(anchor="w", pady=(0, 8))

        self.total_lbl = self._label(inner, "£0.00", size=22, bold=True, color=COLORS["accent"])
        self.total_lbl.pack(anchor="w", pady=(0, 6))

        self.cat_frame = tk.Frame(inner, bg=COLORS["surface"])
        self.cat_frame.pack(fill="x")

    def _build_table(self, parent):
        # filter row
        filter_row = tk.Frame(parent, bg=COLORS["bg"])
        filter_row.pack(fill="x", pady=(0, 8))

        self._label(filter_row, "Month (YYYY-MM):", size=12, color=COLORS["muted"]).pack(side="left")
        self.month_var = tk.StringVar(value=datetime.today().strftime("%Y-%m"))
        tk.Entry(
            filter_row, textvariable=self.month_var, width=10, font=("Helvetica", 12),
            relief="flat", highlightbackground=COLORS["border"], highlightthickness=1, bd=0
        ).pack(side="left", padx=(6, 6), ipady=4)

        tk.Button(
            filter_row, text="Filter", command=self._refresh,
            font=("Helvetica", 11), bg=COLORS["accent_light"], fg=COLORS["accent"],
            relief="flat", cursor="hand2", padx=8, pady=4
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            filter_row, text="All time", command=self._show_all,
            font=("Helvetica", 11), bg=COLORS["bg"], fg=COLORS["muted"],
            relief="flat", cursor="hand2", padx=8, pady=4
        ).pack(side="left")

        # table
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        cols = ("date", "category", "description", "amount")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")

        for col, label, width in [
            ("date",        "Date",        90),
            ("category",    "Category",   110),
            ("description", "Description", 220),
            ("amount",      "Amount (£)",  90),
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=60)

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
            font=("Helvetica", 12), rowheight=30,
            background=COLORS["surface"], fieldbackground=COLORS["surface"],
            foreground=COLORS["text"])
        style.configure("Treeview.Heading",
            font=("Helvetica", 12, "bold"),
            background=COLORS["bg"], foreground=COLORS["muted"], relief="flat")
        style.map("Treeview",
            background=[("selected", COLORS["accent_light"])],
            foreground=[("selected", COLORS["accent"])])

        tk.Button(
            parent, text="Delete selected", command=self._on_delete,
            font=("Helvetica", 12), fg=COLORS["danger"], bg=COLORS["bg"],
            relief="flat", cursor="hand2", pady=6,
        ).pack(anchor="e", pady=(6, 0))

    # ------------------------------------------------------------------ actions

    def _on_add(self):
        raw = self.amount_var.get().strip().lstrip("£")
        try:
            amount = float(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter a positive number.")
            return

        date = self.date_var.get().strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid date", "Date must be YYYY-MM-DD.")
            return

        services.add_expense(amount, self.cat_var.get(), self.desc_var.get().strip(), date)
        self.amount_var.set("")
        self.desc_var.set("")
        self.date_var.set(datetime.today().strftime("%Y-%m-%d"))
        self._refresh()

    def _on_delete(self):
        selected = self.tree.focus()
        if not selected:
            return
        expense_id = self.tree.item(selected)["tags"][0]
        if messagebox.askyesno("Delete", "Delete this expense?"):
            services.delete_expense(expense_id)
            self._refresh()

    # ------------------------------------------------------------------ refresh

    def _refresh(self):
        month = self.month_var.get().strip() or None
        self._load_table(month)
        self._update_summary(month)

    def _show_all(self):
        self.month_var.set("")
        self._load_table(None)
        self._update_summary(None)

    def _load_table(self, month):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in services.get_expenses(month):
            self.tree.insert(
                "", "end",
                values=(row["date"], row["category"], row["description"] or "—", f"{row['amount']:.2f}"),
                tags=(row["id"],),
            )

    def _update_summary(self, month):
        summary = services.get_summary(month)
        self.total_lbl.config(text=f"£{summary['total']:.2f}")

        for widget in self.cat_frame.winfo_children():
            widget.destroy()

        for cat, total in sorted(summary["by_category"].items(), key=lambda x: -x[1]):
            row = tk.Frame(self.cat_frame, bg=COLORS["surface"])
            row.pack(fill="x", pady=1)
            self._label(row, cat, size=11, color=COLORS["muted"]).pack(side="left")
            self._label(row, f"£{total:.2f}", size=11).pack(side="right")


if __name__ == "__main__":
    init_db()
    app = ExpenseApp()
    app.mainloop()
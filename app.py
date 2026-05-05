# app.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import services
from db import init_db
from theme import COLORS, FONTS, SPACING


class ExpenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("900x700")
        self.minsize(750, 600)
        self.configure(bg=COLORS["bg"])
        self._style_ttk()
        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------ ttk global style

    def _style_ttk(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TCombobox",
            fieldbackground=COLORS["surface_alt"],
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["accent"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            insertcolor=COLORS["accent"],
            selectbackground=COLORS["accent"],
            selectforeground=COLORS["bg"],
        )
        style.map("TCombobox",
            fieldbackground=[("readonly", COLORS["surface_alt"])],
            foreground=[("readonly", COLORS["text"])],
        )

        style.configure("Treeview",
            font=FONTS["mono"],
            rowheight=32,
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            borderwidth=0,
        )
        style.configure("Treeview.Heading",
            font=FONTS["subhead"],
            background=COLORS["surface_alt"],
            foreground=COLORS["accent"],
            relief="flat",
            borderwidth=0,
        )
        style.map("Treeview",
            background=[("selected", COLORS["accent_light"])],
            foreground=[("selected", COLORS["accent"])],
        )

        style.configure("Vertical.TScrollbar",
            background=COLORS["surface_alt"],
            troughcolor=COLORS["surface"],
            arrowcolor=COLORS["muted"],
            bordercolor=COLORS["surface"],
        )

    # ------------------------------------------------------------------ helpers

    def _card(self, parent) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

    def _label(self, parent, text, font_key="body", color=None, **kw) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=FONTS[font_key],
            fg=color or COLORS["text"],
            bg=parent.cget("bg"),
            **kw,
        )

    def _entry(self, parent, textvariable) -> tk.Entry:
        return tk.Entry(
            parent,
            textvariable=textvariable,
            font=FONTS["body"],
            relief="flat", bd=0,
            bg=COLORS["surface_alt"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
            highlightthickness=1,
        )

    # ------------------------------------------------------------------ build UI

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS["surface"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._label(header, "  Expense Tracker", font_key="heading",
                    color=COLORS["white"]).pack(side="left", pady=12)
        self._label(header, "Stripe-style Dark  ", font_key="small",
                    color=COLORS["muted"]).pack(side="right", pady=12)

        tk.Frame(self, bg=COLORS["accent"], height=2).pack(fill="x")

        # Body
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=16)

        left = tk.Frame(body, bg=COLORS["bg"], width=260)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True)

        self._build_form(left)
        self._build_summary(left)
        self._build_table(right)

    def _build_form(self, parent):
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 12))

        inner = tk.Frame(card, bg=COLORS["surface"],
                         padx=SPACING["pad_x"], pady=SPACING["pad_y"])
        inner.pack(fill="both")

        self._label(inner, "New expense", font_key="heading",
                    color=COLORS["white"]).pack(anchor="w", pady=(0, 14))

        self._label(inner, "Amount (£)", font_key="small",
                    color=COLORS["muted"]).pack(anchor="w")
        self.amount_var = tk.StringVar()
        self._entry(inner, self.amount_var).pack(fill="x", ipady=7, pady=(3, 10))

        self._label(inner, "Category", font_key="small",
                    color=COLORS["muted"]).pack(anchor="w")
        self.cat_var = tk.StringVar(value=services.CATEGORIES[0])
        ttk.Combobox(
            inner, textvariable=self.cat_var,
            values=services.CATEGORIES, state="readonly",
            font=FONTS["body"],
        ).pack(fill="x", ipady=4, pady=(3, 10))

        self._label(inner, "Description", font_key="small",
                    color=COLORS["muted"]).pack(anchor="w")
        self.desc_var = tk.StringVar()
        self._entry(inner, self.desc_var).pack(fill="x", ipady=7, pady=(3, 10))

        self._label(inner, "Date", font_key="small",
                    color=COLORS["muted"]).pack(anchor="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        DateEntry(
            inner,
            textvariable=self.date_var,
            font=FONTS["body"],
            date_pattern="yyyy-mm-dd",
            background=COLORS["accent"],
            foreground=COLORS["bg"],
            bordercolor=COLORS["border"],
            headersbackground=COLORS["surface_alt"],
            headersforeground=COLORS["accent"],
            selectbackground=COLORS["accent"],
            selectforeground=COLORS["bg"],
            normalbackground=COLORS["surface"],
            normalforeground=COLORS["text"],
            weekendbackground=COLORS["surface"],
            weekendforeground=COLORS["accent"],
            othermonthbackground=COLORS["bg"],
            othermonthforeground=COLORS["muted"],
        ).pack(fill="x", ipady=6, pady=(3, 14))

        tk.Button(
            inner, text="Add expense", command=self._on_add,
            font=FONTS["btn"],
            fg=COLORS["bg"], bg=COLORS["accent"],
            activebackground="#00a844", activeforeground=COLORS["bg"],
            relief="flat", cursor="hand2", pady=10, bd=0,
        ).pack(fill="x")

    def _build_summary(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=COLORS["surface"],
                         padx=SPACING["pad_x"], pady=SPACING["pad_y"])
        inner.pack(fill="both", expand=True)

        self._label(inner, "This month", font_key="subhead",
                    color=COLORS["muted"]).pack(anchor="w", pady=(0, 4))

        self.total_lbl = self._label(inner, "£0.00", font_key="total",
                                     color=COLORS["accent"])
        self.total_lbl.pack(anchor="w", pady=(0, 10))

        tk.Frame(inner, bg=COLORS["border"], height=1).pack(fill="x", pady=(0, 10))

        # Pie chart canvas
        self.fig, self.ax = plt.subplots(figsize=(2.4, 2.4))
        self.fig.patch.set_facecolor(COLORS["surface"])
        self.ax.set_facecolor(COLORS["surface"])

        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=inner)
        self.chart_canvas.get_tk_widget().pack(fill="x")

        # Percentage breakdown labels
        self.pct_frame = tk.Frame(inner, bg=COLORS["surface"])
        self.pct_frame.pack(fill="x", pady=(8, 0))

    def _build_table(self, parent):
        filter_row = tk.Frame(parent, bg=COLORS["bg"])
        filter_row.pack(fill="x", pady=(0, 10))

        self._label(filter_row, "Month:", font_key="small",
                    color=COLORS["muted"]).pack(side="left")

        self.month_var = tk.StringVar(value=datetime.today().strftime("%Y-%m"))
        self._entry(filter_row, self.month_var).pack(
            side="left", padx=(6, 8), ipady=5, ipadx=6)

        tk.Button(
            filter_row, text="Filter", command=self._refresh,
            font=FONTS["small"], fg=COLORS["accent"], bg=COLORS["accent_light"],
            activebackground=COLORS["border"], activeforeground=COLORS["accent"],
            relief="flat", cursor="hand2", padx=12, pady=5, bd=0,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            filter_row, text="All time", command=self._show_all,
            font=FONTS["small"], fg=COLORS["muted"], bg=COLORS["surface"],
            activebackground=COLORS["surface_alt"], activeforeground=COLORS["text"],
            relief="flat", cursor="hand2", padx=12, pady=5, bd=0,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            filter_row, text="Export Excel", command=self._on_export,
            font=FONTS["small"], fg=COLORS["bg"], bg=COLORS["accent"],
            activebackground="#00a844", activeforeground=COLORS["bg"],
            relief="flat", cursor="hand2", padx=12, pady=5, bd=0,
        ).pack(side="right")

        card = self._card(parent)
        card.pack(fill="both", expand=True)

        cols = ("date", "category", "description", "amount")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")

        for col, label, width, anchor in [
            ("date",        "Date",        95,  "w"),
            ("category",    "Category",    115, "w"),
            ("description", "Description", 240, "w"),
            ("amount",      "Amount (£)",  100, "e"),
        ]:
            self.tree.heading(col, text=label, anchor=anchor)
            self.tree.column(col, width=width, minwidth=60, anchor=anchor)

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Button(
            parent, text="Delete selected", command=self._on_delete,
            font=FONTS["small"], fg=COLORS["danger"], bg=COLORS["bg"],
            activeforeground=COLORS["danger"], activebackground=COLORS["bg"],
            relief="flat", cursor="hand2", pady=6, bd=0,
        ).pack(anchor="e", pady=(8, 0))

    # ------------------------------------------------------------------ pie chart

    def _update_chart(self, by_category: dict, total: float):
        self.ax.clear()

        if not by_category:
            self.ax.text(
                0.5, 0.5, "No data", ha="center", va="center",
                color=COLORS["muted"], fontsize=11,
                transform=self.ax.transAxes,
            )
            self.ax.axis("off")
            self.chart_canvas.draw()
            for w in self.pct_frame.winfo_children():
                w.destroy()
            return

        PIE_COLORS = [
            "#00c853", "#1de9b6", "#00b0ff",
            "#d500f9", "#ff6d00", "#ffea00",
            "#ff1744",
        ]

        labels = list(by_category.keys())
        values = list(by_category.values())
        colors = PIE_COLORS[:len(labels)]

        wedges, _ = self.ax.pie(
            values,
            colors=colors,
            startangle=90,
            wedgeprops={"linewidth": 2, "edgecolor": COLORS["surface"]},
        )

        self.ax.axis("equal")
        self.fig.tight_layout(pad=0.5)
        self.chart_canvas.draw()

        # Percentage labels
        for w in self.pct_frame.winfo_children():
            w.destroy()

        for i, (cat, val) in enumerate(zip(labels, values)):
            pct = (val / total * 100) if total else 0
            row = tk.Frame(self.pct_frame, bg=COLORS["surface"])
            row.pack(fill="x", pady=1)

            dot = tk.Label(row, text="●", fg=PIE_COLORS[i % len(PIE_COLORS)],
                           bg=COLORS["surface"], font=FONTS["small"])
            dot.pack(side="left", padx=(0, 4))

            self._label(row, cat, font_key="small",
                        color=COLORS["muted"]).pack(side="left")
            self._label(row, f"{pct:.1f}%", font_key="small",
                        color=COLORS["text"]).pack(side="right")

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

        services.add_expense(
            amount,
            self.cat_var.get(),
            self.desc_var.get().strip(),
            self.date_var.get(),
        )
        self.amount_var.set("")
        self.desc_var.set("")
        self._refresh()

    def _on_delete(self):
        selected = self.tree.focus()
        if not selected:
            return
        expense_id = self.tree.item(selected)["tags"][0]
        if messagebox.askyesno("Delete", "Delete this expense?"):
            services.delete_expense(expense_id)
            self._refresh()

    def _on_export(self):
        month = self.month_var.get().strip() or None
        label = month if month else "all_time"

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx")],
            initialfile=f"expenses_{label}.xlsx",
        )
        if not path:
            return

        try:
            services.export_to_excel(path, month)
            messagebox.showinfo("Exported", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

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
                values=(
                    row["date"],
                    row["category"],
                    row["description"] or "—",
                    f"{row['amount']:.2f}",
                ),
                tags=(row["id"],),
            )

    def _update_summary(self, month):
        summary = services.get_summary(month)
        self.total_lbl.config(text=f"£{summary['total']:.2f}")
        self._update_chart(summary["by_category"], summary["total"])


if __name__ == "__main__":
    init_db()
    app = ExpenseApp()
    app.mainloop()
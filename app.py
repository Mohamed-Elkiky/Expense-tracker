# app.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import services
from db import init_db
from theme import DARK, LIGHT, FONTS, SPACING


class ExpenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("900x700")
        self.minsize(750, 600)
        self.is_dark = True
        self.C = DARK
        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------ theme

    def _apply_theme(self):
        self.C = DARK if self.is_dark else LIGHT
        self._style_ttk()
        self.destroy()
        self.__init__()

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self.C = DARK if self.is_dark else LIGHT
        self._style_ttk()
        # rebuild UI with new colors
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
        self._refresh()
        self._draw_toggle_icon()

    # ------------------------------------------------------------------ ttk style

    def _style_ttk(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TCombobox",
            fieldbackground=self.C["surface_alt"],
            background=self.C["surface_alt"],
            foreground=self.C["text"],
            arrowcolor=self.C["accent"],
            bordercolor=self.C["border"],
            lightcolor=self.C["border"],
            darkcolor=self.C["border"],
            insertcolor=self.C["accent"],
            selectbackground=self.C["accent"],
            selectforeground=self.C["bg"],
        )
        style.map("TCombobox",
            fieldbackground=[("readonly", self.C["surface_alt"])],
            foreground=[("readonly", self.C["text"])],
        )

        style.configure("Treeview",
            font=FONTS["mono"],
            rowheight=32,
            background=self.C["surface"],
            fieldbackground=self.C["surface"],
            foreground=self.C["text"],
            borderwidth=0,
        )
        style.configure("Treeview.Heading",
            font=FONTS["subhead"],
            background=self.C["surface_alt"],
            foreground=self.C["accent"],
            relief="flat",
            borderwidth=0,
        )
        style.map("Treeview",
            background=[("selected", self.C["accent_light"])],
            foreground=[("selected", self.C["accent"])],
        )

        style.configure("Vertical.TScrollbar",
            background=self.C["surface_alt"],
            troughcolor=self.C["surface"],
            arrowcolor=self.C["muted"],
            bordercolor=self.C["surface"],
        )

    # ------------------------------------------------------------------ helpers

    def _card(self, parent) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.C["surface"],
            highlightbackground=self.C["border"],
            highlightthickness=1,
        )

    def _label(self, parent, text, font_key="body", color=None, **kw) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=FONTS[font_key],
            fg=color or self.C["text"],
            bg=parent.cget("bg"),
            **kw,
        )

    def _entry(self, parent, textvariable) -> tk.Entry:
        return tk.Entry(
            parent,
            textvariable=textvariable,
            font=FONTS["body"],
            relief="flat", bd=0,
            bg=self.C["surface_alt"],
            fg=self.C["text"],
            insertbackground=self.C["accent"],
            highlightbackground=self.C["border"],
            highlightcolor=self.C["accent"],
            highlightthickness=1,
        )

    # ------------------------------------------------------------------ build UI

    def _build_ui(self):
        self.configure(bg=self.C["bg"])
        self._style_ttk()

        # Header
        header = tk.Frame(self, bg=self.C["surface"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Sun/moon toggle button (canvas drawn)
        self.toggle_canvas = tk.Canvas(
            header, width=52, height=26,
            bg=self.C["surface"], highlightthickness=0, cursor="hand2",
        )
        self.toggle_canvas.pack(side="left", padx=12, pady=12)
        self.toggle_canvas.bind("<Button-1>", lambda e: self._toggle_theme())
        self._draw_toggle_icon()

        self._label(header, "Expense Tracker", font_key="heading",
                    color=self.C["text"]).pack(side="left", pady=12)
        self._label(
            header,
            "Dark mode" if self.is_dark else "Light mode",
            font_key="small", color=self.C["muted"]
        ).pack(side="right", padx=12, pady=12)

        # Green accent line
        tk.Frame(self, bg=self.C["accent"], height=2).pack(fill="x")

        # Body
        body = tk.Frame(self, bg=self.C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=16)

        left = tk.Frame(body, bg=self.C["bg"], width=260)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=self.C["bg"])
        right.pack(side="right", fill="both", expand=True)

        self._build_form(left)
        self._build_summary(left)
        self._build_table(right)

    # ------------------------------------------------------------------ sun/moon icon

    def _draw_toggle_icon(self):
        c = self.toggle_canvas
        c.delete("all")
        c.configure(bg=self.C["surface"])

        # pill background
        pill_color = self.C["accent"] if self.is_dark else self.C["border"]
        c.create_oval(0, 2, 24, 24, fill=pill_color, outline="")
        c.create_oval(28, 2, 52, 24, fill=pill_color, outline="")
        c.create_rectangle(12, 2, 40, 24, fill=pill_color, outline="")

        if self.is_dark:
            # Moon — crescent using two overlapping circles
            c.create_oval(28, 4, 50, 22, fill=self.C["bg"], outline="")
            c.create_oval(32, 4, 52, 22, fill=self.C["surface"], outline="")
        else:
            # Sun — circle with rays
            cx, cy, r = 14, 13, 5
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          fill=self.C["surface"], outline="")
            ray_color = self.C["surface"]
            for dx, dy in [
                (0, -9), (0, 9), (-9, 0), (9, 0),
                (-6, -6), (6, -6), (-6, 6), (6, 6),
            ]:
                c.create_line(cx, cy, cx + dx, cy + dy,
                              fill=ray_color, width=1.5)

    # ------------------------------------------------------------------ form

    def _build_form(self, parent):
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 12))

        inner = tk.Frame(card, bg=self.C["surface"],
                         padx=SPACING["pad_x"], pady=SPACING["pad_y"])
        inner.pack(fill="both")

        self._label(inner, "New expense", font_key="heading",
                    color=self.C["text"]).pack(anchor="w", pady=(0, 14))

        self._label(inner, "Amount (£)", font_key="small",
                    color=self.C["muted"]).pack(anchor="w")
        self.amount_var = tk.StringVar()
        self._entry(inner, self.amount_var).pack(fill="x", ipady=7, pady=(3, 10))

        self._label(inner, "Category", font_key="small",
                    color=self.C["muted"]).pack(anchor="w")
        self.cat_var = tk.StringVar(value=services.CATEGORIES[0])
        ttk.Combobox(
            inner, textvariable=self.cat_var,
            values=services.CATEGORIES, state="readonly",
            font=FONTS["body"],
        ).pack(fill="x", ipady=4, pady=(3, 10))

        self._label(inner, "Description", font_key="small",
                    color=self.C["muted"]).pack(anchor="w")
        self.desc_var = tk.StringVar()
        self._entry(inner, self.desc_var).pack(fill="x", ipady=7, pady=(3, 10))

        self._label(inner, "Date", font_key="small",
                    color=self.C["muted"]).pack(anchor="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        DateEntry(
            inner,
            textvariable=self.date_var,
            font=FONTS["body"],
            date_pattern="yyyy-mm-dd",
            background=self.C["accent"],
            foreground=self.C["bg"],
            bordercolor=self.C["border"],
            headersbackground=self.C["surface_alt"],
            headersforeground=self.C["accent"],
            selectbackground=self.C["accent"],
            selectforeground=self.C["bg"],
            normalbackground=self.C["surface"],
            normalforeground=self.C["text"],
            weekendbackground=self.C["surface"],
            weekendforeground=self.C["accent"],
            othermonthbackground=self.C["bg"],
            othermonthforeground=self.C["muted"],
        ).pack(fill="x", ipady=6, pady=(3, 14))

        tk.Button(
            inner, text="Add expense", command=self._on_add,
            font=FONTS["btn"],
            fg=self.C["bg"], bg=self.C["accent"],
            activebackground=self.C["accent"], activeforeground=self.C["bg"],
            relief="flat", cursor="hand2", pady=10, bd=0,
        ).pack(fill="x")

    # ------------------------------------------------------------------ summary

    def _build_summary(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=self.C["surface"],
                         padx=SPACING["pad_x"], pady=SPACING["pad_y"])
        inner.pack(fill="both", expand=True)

        self._label(inner, "This month", font_key="subhead",
                    color=self.C["muted"]).pack(anchor="w", pady=(0, 4))

        self.total_lbl = self._label(inner, "£0.00", font_key="total",
                                     color=self.C["accent"])
        self.total_lbl.pack(anchor="w", pady=(0, 10))

        tk.Frame(inner, bg=self.C["border"], height=1).pack(fill="x", pady=(0, 10))

        # Pie chart
        self.fig, self.ax = plt.subplots(figsize=(2.4, 2.4))
        self.fig.patch.set_facecolor(self.C["surface"])
        self.ax.set_facecolor(self.C["surface"])

        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=inner)
        self.chart_canvas.get_tk_widget().pack(fill="x")

        self.pct_frame = tk.Frame(inner, bg=self.C["surface"])
        self.pct_frame.pack(fill="x", pady=(8, 0))

    # ------------------------------------------------------------------ table

    def _build_table(self, parent):
        filter_row = tk.Frame(parent, bg=self.C["bg"])
        filter_row.pack(fill="x", pady=(0, 10))

        self._label(filter_row, "Month:", font_key="small",
                    color=self.C["muted"]).pack(side="left")

        self.month_var = tk.StringVar(value=datetime.today().strftime("%Y-%m"))
        self._entry(filter_row, self.month_var).pack(
            side="left", padx=(6, 8), ipady=5, ipadx=6)

        tk.Button(
            filter_row, text="Filter", command=self._refresh,
            font=FONTS["small"], fg=self.C["accent"], bg=self.C["accent_light"],
            activebackground=self.C["border"], activeforeground=self.C["accent"],
            relief="flat", cursor="hand2", padx=12, pady=5, bd=0,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            filter_row, text="All time", command=self._show_all,
            font=FONTS["small"], fg=self.C["muted"], bg=self.C["surface"],
            activebackground=self.C["surface_alt"], activeforeground=self.C["text"],
            relief="flat", cursor="hand2", padx=12, pady=5, bd=0,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            filter_row, text="Export Excel", command=self._on_export,
            font=FONTS["small"], fg=self.C["bg"], bg=self.C["accent"],
            activebackground=self.C["accent"], activeforeground=self.C["bg"],
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
            font=FONTS["small"], fg=self.C["danger"], bg=self.C["bg"],
            activeforeground=self.C["danger"], activebackground=self.C["bg"],
            relief="flat", cursor="hand2", pady=6, bd=0,
        ).pack(anchor="e", pady=(8, 0))

    # ------------------------------------------------------------------ pie chart

    def _update_chart(self, by_category: dict, total: float):
        self.ax.clear()
        self.fig.patch.set_facecolor(self.C["surface"])
        self.ax.set_facecolor(self.C["surface"])

        if not by_category:
            # empty grey donut
            self.ax.pie(
                [1],
                colors=[self.C["border"]],
                startangle=90,
                wedgeprops={"linewidth": 2, "edgecolor": self.C["surface"],
                            "width": 0.6},
            )
            self.ax.axis("equal")
            self.fig.tight_layout(pad=0.5)
            self.chart_canvas.draw()
            for w in self.pct_frame.winfo_children():
                w.destroy()
            return

        PIE_COLORS = [
            "#00c853", "#1de9b6", "#00b0ff",
            "#d500f9", "#ff6d00", "#ffea00", "#ff1744",
        ]

        labels = list(by_category.keys())
        values = list(by_category.values())
        colors = PIE_COLORS[:len(labels)]

        self.ax.pie(
            values,
            colors=colors,
            startangle=90,
            wedgeprops={"linewidth": 2, "edgecolor": self.C["surface"],
                        "width": 0.6},
        )

        self.ax.axis("equal")
        self.fig.tight_layout(pad=0.5)
        self.chart_canvas.draw()

        for w in self.pct_frame.winfo_children():
            w.destroy()

        for i, (cat, val) in enumerate(zip(labels, values)):
            pct = (val / total * 100) if total else 0
            row = tk.Frame(self.pct_frame, bg=self.C["surface"])
            row.pack(fill="x", pady=1)

            tk.Label(row, text="●", fg=PIE_COLORS[i % len(PIE_COLORS)],
                     bg=self.C["surface"], font=FONTS["small"]).pack(side="left", padx=(0, 4))
            self._label(row, cat, font_key="small",
                        color=self.C["muted"]).pack(side="left")
            self._label(row, f"{pct:.1f}%", font_key="small",
                        color=self.C["text"]).pack(side="right")

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
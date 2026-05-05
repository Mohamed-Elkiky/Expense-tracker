# services.py
from db import get_connection

CATEGORIES = ["Food", "Transport", "Entertainment", "Health", "Shopping", "Utilities", "Other"]


def add_expense(amount: float, category: str, description: str, date: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        (amount, category, description, date),
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def get_expenses(month: str | None = None) -> list:
    conn = get_connection()
    if month:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date LIKE ? ORDER BY date DESC",
            (f"{month}%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC"
        ).fetchall()
    conn.close()
    return rows


def get_summary(month: str | None = None) -> dict:
    rows = get_expenses(month)
    total = sum(r["amount"] for r in rows)
    by_category: dict[str, float] = {}
    for row in rows:
        by_category[row["category"]] = by_category.get(row["category"], 0) + row["amount"]
    return {"total": total, "by_category": by_category}
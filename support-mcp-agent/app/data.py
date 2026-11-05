"""SQLite demo data. Only use synthetic data; Render free disks are ephemeral."""
import os
import sqlite3
from pathlib import Path

FAQ = {
    "shipping": {
        "title": "Shipping & delivery",
        "answer": "Standard shipping takes 3–5 business days; express shipping takes 1–2 business days. Tracking is available using a demo order ID.",
        "keywords": ["shipping", "ship", "delivery", "deliver", "parcel", "package"],
    },
    "returns": {
        "title": "Returns & exchanges",
        "answer": "Unused items can be returned within 30 days of delivery. Keep the order number and original packaging available.",
        "keywords": ["return", "returns", "exchange", "replace"],
    },
    "refund": {
        "title": "Refund processing",
        "answer": "Approved refunds generally reach the original payment method within 5–7 business days after approval.",
        "keywords": ["refund", "refunded", "money back", "payment", "cashback"],
    },
    "contact": {
        "title": "Contact support",
        "answer": "Support hours are Monday–Friday, 9 AM–6 PM. You can create a demo ticket directly in this application.",
        "keywords": ["contact", "support", "agent", "human", "hours", "help"],
    },
}

DEMO_ORDERS = [
    ("ORD1001", "Wireless Headphones", "Shipped", "2026-11-09", "In transit to destination hub"),
    ("ORD1002", "Smart Watch", "Processing", "2026-11-12", "Packed and awaiting carrier pickup"),
    ("ORD1003", "Laptop Stand", "Delivered", "2026-11-02", "Delivered to recipient"),
]


def db_path():
    return os.environ.get("DB_PATH", "/tmp/support_agent_mvp.db")


def connect():
    path = db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY, product TEXT NOT NULL, status TEXT NOT NULL,
            eta TEXT NOT NULL, detail TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL,
            issue TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tool TEXT NOT NULL,
            success INTEGER NOT NULL, latency_ms INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        conn.executemany(
            "INSERT OR IGNORE INTO orders (id,product,status,eta,detail) VALUES (?,?,?,?,?)", DEMO_ORDERS
        )


def lookup_order(order_id: str):
    with connect() as conn:
        row = conn.execute(
            "SELECT id, product, status, eta, detail FROM orders WHERE id = ?",
            (order_id.strip().upper(),),
        ).fetchone()
    return dict(row) if row else None


def list_demo_orders():
    with connect() as conn:
        rows = conn.execute("SELECT id,product,status,eta,detail FROM orders ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def search_faq(topic: str):
    q = topic.casefold()
    scores = []
    for category, record in FAQ.items():
        score = sum(2 if word == q.strip() else 1 for word in record["keywords"] if word in q)
        if score:
            scores.append((score, category, record))
    if not scores:
        return {"found": False, "category": "unknown", "title": "No matching policy", "answer": "I couldn't find a matching policy. Try shipping, returns, refunds, or contact support."}
    _, category, record = max(scores, key=lambda x: x[0])
    return {"found": True, "category": category, "title": record["title"], "answer": record["answer"]}


def create_ticket(email: str, issue: str):
    email = email.strip().lower()
    issue = issue.strip()
    if len(email) > 254 or "@" not in email or "." not in email.split("@")[-1]:
        return {"error": "Please provide a valid email address."}
    if not 10 <= len(issue) <= 1200:
        return {"error": "Describe your issue in 10–1200 characters."}
    with connect() as conn:
        row = conn.execute(
            "INSERT INTO tickets (email,issue) VALUES (?,?)", (email, issue)
        )
        ticket_number = row.lastrowid
    return {"ticket_id": f"TKT-{ticket_number:05d}", "status": "Open", "email": email}


def lookup_ticket(ticket_id: str, email: str):
    try:
        number = int(ticket_id.upper().replace("TKT-", ""))
    except ValueError:
        return {"error": "Invalid ticket ID."}
    with connect() as conn:
        row = conn.execute(
            "SELECT id,status,created_at FROM tickets WHERE id = ? AND lower(email) = ?",
            (number, email.strip().lower()),
        ).fetchone()
    if row is None:
        return {"error": "No matching ticket. Check both the ticket ID and email."}
    return {"ticket_id": f"TKT-{row['id']:05d}", "status": row["status"], "created_at": row["created_at"]}


def record_interaction(tool: str, success: bool, latency_ms: int):
    # Never log raw prompts, email addresses, or ticket contents in analytics.
    with connect() as conn:
        conn.execute(
            "INSERT INTO interactions (tool, success, latency_ms) VALUES (?,?,?)",
            (tool[:60], int(success), max(0, latency_ms)),
        )


def get_metrics():
    with connect() as conn:
        row = conn.execute("""SELECT COUNT(*) total, COALESCE(SUM(success),0) successful,
                 COALESCE(AVG(latency_ms),0) avg_latency FROM interactions""").fetchone()
        ticket_count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        recent = conn.execute("""SELECT tool, success, latency_ms, created_at
            FROM interactions ORDER BY id DESC LIMIT 6""").fetchall()
    total = row["total"]
    return {
        "requests": total,
        "success_rate": round(row["successful"] * 100 / total) if total else 0,
        "avg_latency_ms": round(row["avg_latency"]),
        "tickets": ticket_count,
        "recent": [dict(item) for item in recent],
    }

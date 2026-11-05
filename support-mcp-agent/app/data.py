import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv('DB_PATH', '/tmp/support_agent.db')
FAQ = {
    'shipping': 'Standard shipping takes 3–5 business days. Express shipping takes 1–2 business days.',
    'returns': 'Returns are accepted within 30 days of delivery for unused products.',
    'refund': 'Approved refunds usually reach the original payment method in 5–7 business days.',
    'contact': 'Support is available Monday–Friday, 9 AM–6 PM. You can create a support ticket here.',
}

def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, customer TEXT, status TEXT, eta TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, issue TEXT, status TEXT DEFAULT "open")')
        conn.executemany('INSERT OR IGNORE INTO orders VALUES (?,?,?,?)', [
            ('ORD1001','Asha','Shipped','2026-11-09'),
            ('ORD1002','Ravi','Processing','2026-11-12'),
            ('ORD1003','Priya','Delivered','2026-11-02'),
        ])

def lookup_order(order_id: str):
    with connect() as conn:
        row = conn.execute('SELECT id, status, eta FROM orders WHERE id=?', (order_id.upper(),)).fetchone()
        return dict(row) if row else None

def create_ticket(email: str, issue: str):
    with connect() as conn:
        cursor = conn.execute('INSERT INTO tickets (email,issue) VALUES (?,?)', (email, issue))
        return {'ticket_id': cursor.lastrowid, 'status': 'open'}

import pytest
from app.data import (init_db, lookup_order, list_demo_orders, search_faq,
                      create_ticket, lookup_ticket, get_metrics, record_interaction)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "demo.db"))
    init_db()


def test_seeded_demo_orders():
    assert len(list_demo_orders()) == 3
    assert lookup_order("ord1001")["status"] == "Shipped"
    assert lookup_order("INVALID") is None


def test_search_faq():
    assert search_faq("What is your refund policy?")["category"] == "refund"
    assert search_faq("I want to return this")["category"] == "returns"
    assert search_faq("xyzzzz")["found"] is False


def test_ticket_creation_lookup_requires_email():
    created = create_ticket("demo@example.com", "My parcel arrived damaged")
    ticket = created["ticket_id"]
    assert ticket.startswith("TKT-")
    assert lookup_ticket(ticket, "demo@example.com")["status"] == "Open"
    assert "error" in lookup_ticket(ticket, "other@example.com")


def test_ticket_validation():
    assert "error" in create_ticket("bad", "Too short")


def test_metrics_do_not_capture_content():
    record_interaction("get_order_status", True, 45)
    record_interaction("search_knowledge_base", False, 20)
    metrics = get_metrics()
    assert metrics["requests"] == 2
    assert metrics["success_rate"] == 50
    assert len(metrics["recent"]) == 2

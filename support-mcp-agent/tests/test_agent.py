import asyncio
import os
from app.agent import plan, rules_plan, answer_for, safe_tool_args


def test_order_intent():
    tool, args = rules_plan("Where is order ORD1001?")
    assert tool == "get_order_status"
    assert args["order_id"] == "ORD1001"


def test_refund_faq():
    tool, args = rules_plan("What is your refund policy?")
    assert tool == "search_knowledge_base"
    assert "refund" in args["topic"]


def test_ticket_create():
    tool, args = rules_plan("Create ticket demo@example.com my parcel arrived damaged")
    assert tool == "open_support_ticket"
    assert args["email"] == "demo@example.com"


def test_ticket_lookup():
    tool, args = rules_plan("Check TKT-00001 with demo@example.com")
    assert tool == "get_ticket_status"
    assert args["ticket_id"] == "TKT-00001"


def test_missing_lookup_email_does_not_hit_tool():
    assert rules_plan("Check TKT-00001")[0] == "search_knowledge_base"


def test_rules_when_ollama_absent(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    assert asyncio.run(plan("Track ORD1002"))[2] == "Rules"


def test_reject_unfilled_llm_args():
    assert safe_tool_args("open_support_ticket", {"email": "demo@example.com"}) is None


def test_grounded_answer():
    assert "ORD1001" in answer_for("get_order_status", {
        "id": "ORD1001", "product": "Headphones", "status": "Shipped",
        "eta": "2026-11-09", "detail": "In transit"
    })


def test_gemini_planner_selected_with_key(monkeypatch):
    from app import agent
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-only-in-unit-tests")
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    monkeypatch.setattr(agent, "_gemini_request", lambda key, message: {
        "tool": "get_order_status", "args": {"order_id": "ORD1001"}
    })
    tool, args, planner = asyncio.run(agent.plan("Where is order ORD1001?"))
    assert (tool, args, planner) == ("get_order_status", {"order_id": "ORD1001"}, "Gemini")


def test_gemini_cannot_invent_order_id(monkeypatch):
    from app import agent
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-only-in-unit-tests")
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    monkeypatch.setattr(agent, "_gemini_request", lambda key, message: {
        "tool": "get_order_status", "args": {"order_id": "ORD9999"}
    })
    tool, args, planner = asyncio.run(agent.plan("Where is order ORD1001?"))
    assert args["order_id"] == "ORD1001"
    assert planner == "Gemini"


def test_gemini_bad_key_uses_safe_fallback(monkeypatch):
    from app import agent
    monkeypatch.setenv("GEMINI_API_KEY", "invalid-test-key")
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    def failed(*args):
        raise ValueError("API key rejected")
    monkeypatch.setattr(agent, "_gemini_request", failed)
    tool, args, planner = asyncio.run(agent.plan("What is your refund policy?"))
    assert tool == "search_knowledge_base"
    assert planner == "Rules"


def test_reject_gemini_ticket_without_explicit_intent():
    from app.agent import validated_llm_plan
    assert validated_llm_plan({"tool": "open_support_ticket", "args": {
        "email": "demo@example.com", "issue": "hello"
    }}, "My email is demo@example.com") is None

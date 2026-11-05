"""Integration smoke test. Start uvicorn, then run python smoke_test.py.
Set BASE_URL=https://<your-render-url> to test the deployed project.
"""
import os
import sys
import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
CASES = [
    ("Where is order ORD1001?", "get_order_status"),
    ("What is your refund policy?", "search_knowledge_base"),
    ("Create ticket demo@example.com my parcel arrived damaged", "open_support_ticket"),
]


def main():
    try:
        with httpx.Client(base_url=BASE_URL, timeout=50.0, follow_redirects=True) as client:
            health = client.get("/health")
            health.raise_for_status()
            assert health.json()["status"] == "ok"
            for message, tool in CASES:
                r = client.post("/api/chat", json={"message": message})
                r.raise_for_status()
                result = r.json()
                assert result["tool_used"] == tool, result
                assert result["success"], result
                print(f"PASS {tool}: {result['answer']}")
                if tool == "open_support_ticket":
                    ticket = result["tool_result"]["ticket_id"]
                    follow = client.post("/api/chat", json={
                        "message": f"Check ticket status {ticket} for demo@example.com"
                    })
                    follow.raise_for_status()
                    value = follow.json()
                    assert value["tool_used"] == "get_ticket_status", value
                    assert value["success"], value
                    print(f"PASS get_ticket_status: {value['answer']}")
            stats = client.get("/api/metrics")
            stats.raise_for_status()
            assert stats.json()["requests"] >= 4
            print("PASS /api/metrics")
            print("ALL 4 REAL MCP TOOLS PASSED")
            return 0
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

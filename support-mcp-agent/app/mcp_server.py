"""Four genuine Model Context Protocol tools served over Streamable HTTP."""
from mcp.server.fastmcp import FastMCP
from app.data import search_faq, lookup_order, create_ticket, lookup_ticket

mcp = FastMCP("SupportDesk MCP", stateless_http=True, json_response=True)


@mcp.tool()
def search_knowledge_base(topic: str) -> dict:
    """Answer a support policy question about shipping, returns, refunds or contact hours."""
    return search_faq(topic)


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """Track a demo shipment with an order ID such as ORD1001."""
    return lookup_order(order_id) or {"error": "Demo order not found."}


@mcp.tool()
def open_support_ticket(email: str, issue: str) -> dict:
    """Create a demo customer support ticket from an email and issue description."""
    return create_ticket(email, issue)


@mcp.tool()
def get_ticket_status(ticket_id: str, email: str) -> dict:
    """Look up demo support ticket status; requires both TKT-00001 and the same email."""
    return lookup_ticket(ticket_id, email)

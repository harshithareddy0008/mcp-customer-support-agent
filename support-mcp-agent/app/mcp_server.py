"""Real MCP tools exposed over Streamable HTTP at /mcp."""
from mcp.server.fastmcp import FastMCP
from app.data import FAQ, lookup_order, create_ticket

mcp = FastMCP('Customer Support Tools', stateless_http=True, json_response=True)

@mcp.tool()
def search_knowledge_base(topic: str) -> str:
    """Search the customer support knowledge base for shipping, returns, refunds, or contact."""
    topic = topic.lower()
    for key, answer in FAQ.items():
        if key in topic or (key == 'returns' and 'return' in topic):
            return answer
    return 'No matching policy found. Consider creating a support ticket.'

@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """Find the shipping status of a demo order ID, such as ORD1001."""
    return lookup_order(order_id) or {'error': 'Order not found'}

@mcp.tool()
def open_support_ticket(email: str, issue: str) -> dict:
    """Create a support ticket for a customer email and issue."""
    return create_ticket(email, issue)

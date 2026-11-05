"""Tool-using agent: optional local Ollama planner, reliable zero-key fallback."""
import json
import os
import re
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

TOOLS = ['search_knowledge_base', 'get_order_status', 'open_support_ticket']

async def plan(message: str):
    """Use an open-source Ollama model when configured, otherwise a transparent rules planner."""
    host = os.getenv('OLLAMA_URL', '').rstrip('/')
    if host:
        prompt = ('Choose exactly one tool for this customer request. Return ONLY JSON with keys '
                  'tool and args. Tools: search_knowledge_base(topic), get_order_status(order_id), '
                  'open_support_ticket(email,issue). If not enough details for ticket, use '
                  'search_knowledge_base. User: ' + message)
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.post(host + '/api/generate', json={
                    'model': os.getenv('OLLAMA_MODEL', 'llama3.2:1b'),
                    'prompt': prompt, 'stream': False, 'format': 'json'})
                response.raise_for_status()
                parsed = json.loads(response.json()['response'])
                if parsed.get('tool') in TOOLS and isinstance(parsed.get('args'), dict):
                    return parsed['tool'], parsed['args'], 'ollama'
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            pass
    lower = message.lower()
    order = re.search(r'\bORD\s*\d+\b', message, re.I)
    email = re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', message)
    if ('ticket' in lower or 'complaint' in lower or 'human' in lower) and email:
        return 'open_support_ticket', {'email': email.group(), 'issue': message}, 'rules'
    if order:
        return 'get_order_status', {'order_id': re.sub(r'\s+', '', order.group()).upper()}, 'rules'
    return 'search_knowledge_base', {'topic': lower}, 'rules'

async def run_agent(message: str, base_url: str):
    tool, args, planner = await plan(message)
    # IMPORTANT: Tools are actually called through the MCP protocol, not direct Python calls.
    async with streamablehttp_client(base_url.rstrip('/') + '/mcp') as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments=args)
    parts = [getattr(block, 'text', '') for block in result.content]
    raw = '\n'.join(parts)
    try:
        value = json.loads(raw)
    except ValueError:
        value = raw
    if tool == 'get_order_status':
        if isinstance(value, dict) and 'error' not in value:
            answer = f"Order {value['id']} is {value['status']}. Estimated delivery: {value['eta']}."
        else:
            answer = 'I could not find that order. Try ORD1001, ORD1002, or ORD1003.'
    elif tool == 'open_support_ticket':
        if isinstance(value, dict) and 'ticket_id' in value:
            answer = f"Support ticket #{value['ticket_id']} created successfully. Our team will review it."
        else:
            answer = 'Unable to create a ticket right now.'
    else:
        answer = value if isinstance(value, str) else str(value)
        if 'No matching policy' in answer:
            answer += ' Try asking about shipping, returns, or refunds. To open a ticket, include your email and say “create ticket”.'
    return {'answer': answer, 'tool_used': tool, 'planner': planner, 'tool_result': value}

# SupportDesk AI — MCP Customer Support MVP

**[Live Demo](https://mcp-customer-support-agent.onrender.com/) · [Source Repository](https://github.com/harshithareddy0008/mcp-customer-support-agent)**

An open-source, portfolio-ready customer support assistant built using **Python, FastAPI, the official Model Context Protocol (MCP) SDK, SQLite and a responsive dashboard**. Gemini API support (optional free tier), Ollama support, and an offline rules fallback.

> The free deployed demo may sleep and its ephemeral database resets on restart. Ticket/order content is synthetic. This is a demo, not a production customer support service.

## What it demonstrates

- A **real MCP client and server**: the FastAPI agent opens a Streamable HTTP `ClientSession`, calls an MCP tool, and converts the tool response into a grounded customer reply.
- **Four support workflows**: FAQ retrieval, order lookup, ticket creation, and ticket status lookup.
- **Visible execution trace**: selected MCP tool, planner type, execution time and a live activity panel.
- **Dashboard KPIs**: total agent calls, tool success percentage, average execution time, and ticket count.
- **Real development workflow**: GitHub Actions runs unit tests and 4-tool MCP integration checks. Render can auto-deploy after checks pass.

![No screenshots yet](https://img.shields.io/badge/Build-FastAPI%20%2B%20MCP-b7ef81?style=flat-square)

## Architecture

```text
Browser UI (HTML, CSS, vanilla JavaScript)
  | POST /api/chat                       GET /api/metrics, /api/demo/orders, /api/knowledge
  v
FastAPI App
  | Agent planner -> Gemini (when key set) / Ollama / rules fallback
  v
MCP ClientSession -> Streamable HTTP POST http://127.0.0.1:$PORT/mcp
  v
Mounted FastMCP server (same web process)
  |-- search_knowledge_base(topic)
  |-- get_order_status(order_id)
  |-- open_support_ticket(email, issue)
  |-- get_ticket_status(ticket_id, email)
  v
SQLite demo data -> grounded tool result -> customer response
```

The planner is **deterministic by default**; it is not an autonomous LLM agent in this mode. Adding a valid Gemini API key enables LLM-selected MCP tools; a reachable Ollama server is also supported. **LangChain and LangGraph are not used in this release**.

## Local development

Requires **Python 3.11**.

```bash
cd support-mcp-agent
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. Try the demo questions:

1. `Where is order ORD1001?`
2. `What is your refund policy?`
3. `Create ticket demo@example.com my parcel arrived damaged`
4. `Check ticket status TKT-00001 for demo@example.com` (use the actual ticket ID shown by step 3)

Health: `/health` · API docs: `/docs` · MCP endpoint: `/mcp` (JSON-RPC, not a browser GET page)


## Enable Gemini LLM (free-tier API; model is **not open source**)

1. Visit [Google AI Studio API keys](https://aistudio.google.com/apikey), sign in, and create/copy an API key.
2. Inside `support-mcp-agent/`, make a copy of `.env.example` named `.env` (this file is ignored by Git).
3. Set these lines in `.env` (paste **your** key, not a placeholder):

   ```dotenv
   GEMINI_API_KEY=YOUR_REAL_GEMINI_API_KEY
   GEMINI_MODEL=gemini-2.5-flash-lite
   ```

4. Run `pip install -r requirements.txt` and `uvicorn app.main:app --reload` locally. The agent activity panel will show `Gemini planner` if the LLM call succeeds; on quota/errors it safely falls back to `Rules`.
5. For **Render**, add a **secret** via Dashboard → Service → Environment → Add Environment Variable: `GEMINI_API_KEY` with your actual key; optionally `GEMINI_MODEL=gemini-2.5-flash-lite`. Save and redeploy. A local `.env` is **not uploaded** to Render, even after `git push`.

Never commit `.env` or paste the key into README, GitHub issues, or frontend JavaScript. Google offers a limited free tier (model/rate limits vary); verify current pricing and data-use terms at https://ai.google.dev/gemini-api/docs/pricing . Synthetic customer data only.

## Tests

```bash
cd support-mcp-agent
pip install pytest
python -m pytest -q tests
# In a SECOND terminal, run uvicorn first, then:
python smoke_test.py
```

The smoke test calls all four tools **through the actual MCP protocol**. CI runs it automatically on commits and PRs.

## Deploy to existing GitHub + Render

Your current GitHub repo has a `support-mcp-agent` subfolder; the root-level `render.yaml` accounts for that with `rootDir: support-mcp-agent`.

1. Copy the contents of this ZIP **into the root of your local git clone**, replacing existing files. Do not create a second `support-mcp-agent` folder.
2. Commit and push to `main` (commands below).
3. In existing Render Web Service → **Settings**:
   - Repository: `harshithareddy0008/mcp-customer-support-agent`
   - Branch: `main`
   - Root Directory: `support-mcp-agent`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Auto-Deploy: **After CI Checks Pass** (recommended) or **On Commit** (fastest)
4. Next push triggers a build/deployment automatically. **Do not create a duplicate Render service.**

```bash
git clone https://github.com/harshithareddy0008/mcp-customer-support-agent.git
cd mcp-customer-support-agent
# Copy extracted files here, preserving the support-mcp-agent/ and .github/ folders.
git add .
git commit -m "feat: build SupportDesk MCP agent MVP dashboard"
git push origin main
```

For a **new** service created from the root-level Blueprint file, Render uses `autoDeployTrigger: checksPass` (deploy when CI passes). Render's auto-deploy setting is stored per service, so uploading YAML alone does not change an already-created manual Web Service.

## Source structure

```text
.github/workflows/ci.yml        -> Unit tests + real MCP smoke tests on push
render.yaml                     -> Blueprint: rootDir + auto-deploy after CI
support-mcp-agent/
  app/main.py                   -> API endpoints, lifecycle, MCP ASGI mount
  app/agent.py                  -> Planner and MCP ClientSession
  app/mcp_server.py             -> Four MCP tools
  app/data.py                   -> SQLite operations and synthetic data
  static/index.html            -> User-facing support workspace
  static/style.css             -> Responsive interface design
  static/app.js                -> Browser chat, tools, ticket lookup, metrics
  tests/                       -> Unit tests
  smoke_test.py                -> Four real MCP integration checks
  requirements.txt             -> Python dependencies
  .python-version              -> Render Python version pin
```

## Limitations and security

- Public demo; **no login, abuse prevention or real customer verification**. Never use real customer data. The synthetic orders are intentionally public.
- Tickets are scoped by email for lookup, but email knowledge is not authentication; this is not suitable for production customer data.
- SQLite on Render's free ephemeral filesystem can reset on restarts/redeploys. For a real deployment, use PostgreSQL, auth and persistent storage.
- The publicly mounted MCP endpoint is not authenticated; do not attach privileged production tools or secrets to it. Internal agent calls use localhost. Restrict access before adding powerful integrations.
- Without a Gemini API key or reachable Ollama server, the project uses a rules planner. Gemini routes tool calls using the LLM; it does not replace the real MCP client/server.

## Interview pitch

"I built a customer support MVP with FastAPI and the official MCP SDK. A planner selects one of four tools, and an MCP ClientSession invokes it over Streamable HTTP. The dashboard visualizes which tool was called and shows live response metrics. I added SQLite for demo data, GitHub Actions tests, and auto-deployment to Render. With GEMINI_API_KEY configured server-side, Gemini plans tool calls; without it, the app falls back to rules. It supports optional Ollama too."

License: MIT (see `support-mcp-agent/LICENSE`).

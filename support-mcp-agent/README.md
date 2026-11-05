# MCP Customer Support Agent 🤖

A **beginner-friendly, open-source Agentic AI + MCP** portfolio project. Includes a browser chat UI, FastAPI backend, real Model Context Protocol (MCP) server and client, three tools, SQLite demo data, and optional open-source Ollama planning.

## Architecture

```text
Browser UI → POST /api/chat → Agent planner (Ollama optional; rules fallback)
                                    ↓
                          MCP ClientSession
                                    ↓ Streamable HTTP
                            /mcp MCP Server
                                    ↓
               Knowledge base | Order lookup | Support ticket
                                    ↓
                              SQLite / Python
```

**Important:** Without Ollama this is a **rule-based tool-using agent**, not an LLM-driven autonomous agent. MCP calls are real in both modes. Ollama can make tool selection LLM-driven when an accessible Ollama server is configured. The default mode works with **zero API keys** on Render.

## Features
- Real MCP server with `search_knowledge_base`, `get_order_status`, `open_support_ticket` tools
- MCP client connects using Streamable HTTP and invokes selected tool
- Free browser UI showing which MCP tool was used
- SQLite demo orders `ORD1001`, `ORD1002`, `ORD1003`
- Optional Ollama model (`llama3.2:1b`) for LLM-based tool planning
- Render Blueprint config and `/health` endpoint

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and try:
- `Where is order ORD1001?`
- `What is your return policy?`
- `Create ticket test@example.com my package is damaged`

MCP endpoint: `http://localhost:8000/mcp/` (Streamable HTTP; use an MCP client, not a browser GET page).

## Optional open-source LLM with Ollama

Install Ollama locally, then run `ollama pull llama3.2:1b`. Set `OLLAMA_URL=http://localhost:11434` and `OLLAMA_MODEL=llama3.2:1b` in your environment before launching FastAPI. On a remote host, Ollama must be reachable **from the backend**, not your browser. For production, use a securely hosted model endpoint and avoid exposing Ollama publicly.

## GitHub upload

Create an empty public repository in GitHub, then run in the extracted project folder:

```bash
git init
git add .
git commit -m "Build MCP customer support agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mcp-customer-support-agent.git
git push -u origin main
```

## Deploy to Render (free tier where available)

1. Sign into Render and choose **New → Blueprint**; connect your GitHub repo.
2. Select the repo containing `render.yaml`, review the settings and deploy.
3. Or choose **New → Web Service**, runtime Python, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Visit the generated `https://...onrender.com` URL. Verify `/health` returns `{"status":"ok"}`.

**Limitations:** Render free instances can sleep and have ephemeral disks. Demo orders are re-seeded on restart, and support tickets can be lost on redeploy/restart. Use managed Postgres for persistent production tickets. The sample ticket endpoint has no login, spam protection, or customer verification and is for demonstration only. Never store sensitive customer information here. Default order lookup exposes synthetic demo data only.

## Files
- `app/main.py`: FastAPI routes and MCP server lifecycle
- `app/agent.py`: planner and **real MCP client** tool execution
- `app/mcp_server.py`: MCP tool definitions
- `app/data.py`: SQLite storage and demo knowledge base
- `static/index.html`: frontend UI
- `render.yaml`: one-click Render deployment settings
- `.env.example`: optional environment configuration

## Interview explanation

“Users send messages from the web UI to FastAPI. My agent chooses a tool using an optional open-source Ollama LLM or a fallback planner. It connects as an MCP client to a separately exposed MCP server endpoint using the MCP protocol, invokes a knowledge-base, order-tracking or ticket tool, and returns a grounded result. I deployed the app on Render.”

## License
MIT — see `LICENSE`.

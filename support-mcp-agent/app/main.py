"""FastAPI application, dashboard APIs and embedded MCP server."""
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.data import FAQ, init_db, get_metrics, list_demo_orders, record_interaction
from app.mcp_server import mcp
from app.agent import run_agent

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent

# The MCP sub-application already contains /mcp. Mount at / LAST.
mcp_asgi = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="SupportDesk AI | MCP MVP", version="1.0.0", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=ROOT / "static"), name="assets")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "supportdesk-mcp", "version": "1.0.0"}


@app.get("/api/metrics")
def metrics():
    return get_metrics()


@app.get("/api/demo/orders")
def demo_orders():
    return {"orders": list_demo_orders(), "notice": "Synthetic demo orders only"}


@app.get("/api/knowledge")
def knowledge():
    return {"articles": [
        {"slug": slug, "title": item["title"], "answer": item["answer"]}
        for slug, item in FAQ.items()
    ]}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    started = time.perf_counter()
    port = int(os.getenv("PORT", "8000"))
    try:
        response = await run_agent(body.message.strip(), f"http://127.0.0.1:{port}")
        latency = int((time.perf_counter() - started) * 1000)
        response["latency_ms"] = latency
        record_interaction(response["tool_used"], response["success"], latency)
        return response
    except Exception as exc:
        # Never leak an internal stack trace or credentials to browser users.
        logger.exception("MCP handshake or tool execution failed")
        latency = int((time.perf_counter() - started) * 1000)
        record_interaction("mcp_connection_error", False, latency)
        raise HTTPException(status_code=503, detail="Agent tools are unavailable; please try again shortly.") from exc


# Register last: '/' mount is a catch-all and must not swallow FastAPI routes.
app.mount("/", mcp_asgi)

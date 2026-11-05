
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.data import init_db
from app.mcp_server import mcp
from app.agent import run_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Open Source MCP Customer Support Agent",
    lifespan=lifespan
)

app.mount("/mcp", mcp.streamable_http_app())


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1500)


@app.get("/")
def home():
    return FileResponse(
        Path(__file__).resolve().parent.parent / "static" / "index.html"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    port = int(os.environ.get("PORT", "8000"))

    try:
        return await run_agent(
            body.message,
            f"http://127.0.0.1:{port}"
        )
    except Exception as exc:
        logger.exception("MCP tool call failed")
        raise HTTPException(
            status_code=503,
            detail="MCP tool service temporarily unavailable"
        ) from exc

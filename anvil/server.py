import asyncio
import json
import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from anvil.llm.router import LLMRouter
from anvil.agent.loop import AgentLoop
from anvil.index.indexer import ASTIndexer
from anvil.session.store import SessionStore
from anvil.tools.file_ops import ReadFileTool, EditFileTool, CreateFileTool
from anvil.tools.shell import RunCommandTool
from anvil.tools.search import SearchCodebaseTool
from anvil.tools.git import GitDiffTool, GitCommitTool

app = FastAPI(title="Anvil Engine Server")

class ConfigModel(BaseModel):
    provider: str = "google"
    model: str = "gemini-2.5-flash"
    api_key: str = ""

current_config = ConfigModel()
global_indexer = ASTIndexer()
session_store = SessionStore()

@app.post("/api/config")
async def update_config(cfg: ConfigModel):
    global current_config
    current_config = cfg
    return {"status": "ok", "config": current_config}

@app.get("/api/config")
async def get_config():
    return current_config

@app.get("/api/sessions")
async def list_sessions():
    return session_store.list_sessions()

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    res = session_store.get_session(session_id)
    if not res:
        return {"error": "Session not found"}
    return res

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data_text = await websocket.receive_text()
            req = json.loads(data_text)
            prompt = req.get("prompt", "")
            session_id = str(uuid.uuid4())
            transcript = []
            
            async def send_event(event: dict):
                transcript.append(event)
                await websocket.send_json(event)
                session_store.save_session(
                    session_id=session_id,
                    title=prompt[:40] if prompt else "Untitled Task",
                    model=f"{current_config.provider}/{current_config.model}",
                    transcript=transcript
                )

            try:
                provider = LLMRouter.get_provider(
                    provider_name=current_config.provider,
                    model_name=current_config.model,
                    api_key=current_config.api_key or None
                )
            except Exception as e:
                await websocket.send_json({"type": "error", "data": {"error": f"LLM Initialization Failed: {str(e)} "}})
                continue

            tools = [
                ReadFileTool(),
                EditFileTool(),
                CreateFileTool(),
                RunCommandTool(),
                SearchCodebaseTool(indexer=global_indexer),
                GitDiffTool(),
                GitCommitTool(),
            ]
            
            loop = AgentLoop(provider=provider, tools=tools, on_event_cb=send_event)
            asyncio.create_task(loop.run_task(prompt))
            
    except WebSocketDisconnect:
        pass

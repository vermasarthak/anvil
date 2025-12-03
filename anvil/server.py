import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from anvil.llm.router import LLMRouter
from anvil.agent.loop import AgentLoop
from anvil.index.indexer import ASTIndexer
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

@app.post("/api/config")
async def update_config(cfg: ConfigModel):
    global current_config
    current_config = cfg
    return {"status": "ok", "config": current_config}

@app.get("/api/config")
async def get_config():
    return current_config

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data_text = await websocket.receive_text()
            req = json.loads(data_text)
            prompt = req.get("prompt", "")
            
            async def send_event(event: dict):
                await websocket.send_json(event)

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

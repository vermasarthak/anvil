"""Async Language Server Protocol (LSP) Client for Anvil."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional


class AsyncLSPClient:
    """Async LSP Client communicating with Language Servers via JSON-RPC 2.0 over stdin/stdout."""

    def __init__(self, server_command: List[str], root_uri: str):
        self.server_command = server_command
        self.root_uri = root_uri
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self.initialized = False

    async def start(self):
        """Spawns language server subprocess and begins JSON-RPC reader loop."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception:
            self.process = None

    async def initialize(self) -> Dict[str, Any]:
        """Sends LSP initialize request."""
        params = {
            "processId": None,
            "rootUri": self.root_uri,
            "capabilities": {},
        }
        res = await self.send_request("initialize", params)
        self.initialized = True
        return res

    async def send_request(self, method: str, params: Any) -> Dict[str, Any]:
        """Sends JSON-RPC request and returns response result."""
        self._request_id += 1
        req_id = self._request_id

        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")

        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(header + body)
                await self.process.stdin.drain()
            except Exception:
                pass

        return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "ok", "method": method}}

    async def did_open(self, uri: str, language_id: str, text: str):
        """Sends textDocument/didOpen notification."""
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text,
            }
        }
        msg = {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": params,
        }
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(header + body)
                await self.process.stdin.drain()
            except Exception:
                pass

    async def shutdown(self):
        """Sends LSP shutdown request and terminates language server."""
        if self.initialized:
            await self.send_request("shutdown", None)
            self.initialized = False
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception:
                pass

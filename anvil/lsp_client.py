"""Async Language Server Protocol (LSP) Client for Anvil.

Implements JSON-RPC 2.0 communication over stdin/stdout with Content-Length header parsing,
concurrent request/response ID matching, and notification dispatch.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class LSPError(Exception):
    """Raised when an LSP JSON-RPC request returns an error response."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f"LSP Error [{code}]: {message}")
        self.code = code
        self.message = message
        self.data = data


class LSPUnavailableError(Exception):
    """Raised when the language server process cannot be spawned or is terminated."""


class AsyncLSPClient:
    """Async LSP Client communicating with Language Servers via JSON-RPC 2.0."""

    def __init__(
        self,
        server_command: List[str],
        root_uri: str,
        notification_handler: Optional[Callable[[str, Any], None]] = None,
    ):
        self.server_command = server_command
        self.root_uri = root_uri
        self.notification_handler = notification_handler
        self.process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self.initialized = False
        self._server_capabilities: Dict[str, Any] = {}

    async def start(self):
        """Spawns language server subprocess and begins the JSON-RPC reader loop."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as exc:
            self.process = None
            raise LSPUnavailableError(f"Failed to start LSP server '{self.server_command}': {exc!s}") from exc

        self._reader_task = asyncio.create_task(self._reader_loop())

    async def _reader_loop(self):
        """Asynchronously reads and decodes JSON-RPC messages from LSP stdout."""
        if not self.process or not self.process.stdout:
            return

        reader = self.process.stdout
        try:
            while not reader.at_eof():
                # 1. Parse Headers (Content-Length)
                content_length = None
                while True:
                    line = await reader.readline()
                    if not line:
                        return
                    line_str = line.decode("ascii", errors="replace").strip()
                    if not line_str:
                        # Blank line marks end of headers
                        break
                    if line_str.lower().startswith("content-length:"):
                        parts = line_str.split(":", 1)
                        if len(parts) == 2:
                            content_length = int(parts[1].strip())

                if content_length is None or content_length <= 0:
                    continue

                # 2. Read exact payload length
                payload_bytes = await reader.readexactly(content_length)
                try:
                    msg = json.loads(payload_bytes.decode("utf-8"))
                except Exception as e:
                    logger.warning("Failed to decode LSP JSON payload: %s", e)
                    continue

                # 3. Match Request ID or Dispatch Notification
                req_id = msg.get("id")
                if req_id is not None and req_id in self._pending_requests:
                    future = self._pending_requests.pop(req_id)
                    if not future.done():
                        if "error" in msg:
                            err = msg["error"]
                            future.set_exception(
                                LSPError(err.get("code", -1), err.get("message", "Unknown error"), err.get("data"))
                            )
                        else:
                            future.set_result(msg.get("result"))
                elif "method" in msg:
                    # Notification received from server
                    if self.notification_handler:
                        try:
                            self.notification_handler(msg["method"], msg.get("params"))
                        except Exception as e:
                            logger.error("Error in LSP notification handler: %s", e)
        except asyncio.IncompleteReadError:
            pass
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("Unexpected error in LSP reader loop: %s", exc)

    async def send_request(self, method: str, params: Any, timeout_sec: float = 10.0) -> Any:
        """Sends a JSON-RPC request and awaits the server's response."""
        if not self.process or not self.process.stdin or self.process.returncode is not None:
            raise LSPUnavailableError("LSP server process is not active.")

        self._request_id += 1
        req_id = self._request_id

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_requests[req_id] = fut

        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")

        try:
            self.process.stdin.write(header + body)
            await self.process.stdin.drain()
        except Exception as exc:
            self._pending_requests.pop(req_id, None)
            raise LSPUnavailableError(f"Failed to write to LSP stdin: {exc!s}") from exc

        try:
            result = await asyncio.wait_for(fut, timeout=timeout_sec)
            return result
        except asyncio.TimeoutError as exc:
            self._pending_requests.pop(req_id, None)
            raise TimeoutError(f"LSP request '{method}' (id={req_id}) timed out after {timeout_sec}s") from exc

    async def send_notification(self, method: str, params: Any):
        """Sends a JSON-RPC notification (no response expected)."""
        if not self.process or not self.process.stdin or self.process.returncode is not None:
            raise LSPUnavailableError("LSP server process is not active.")

        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")

        try:
            self.process.stdin.write(header + body)
            await self.process.stdin.drain()
        except Exception as exc:
            raise LSPUnavailableError(f"Failed to write notification to LSP stdin: {exc!s}") from exc

    async def initialize(self) -> Dict[str, Any]:
        """Sends LSP initialize request and tracks capabilities."""
        params = {
            "processId": None,
            "rootUri": self.root_uri,
            "capabilities": {
                "textDocument": {
                    "hover": {"contentFormat": ["plaintext", "markdown"]},
                    "completion": {"completionItem": {"snippetSupport": True}},
                }
            },
        }
        res = await self.send_request("initialize", params)
        self.initialized = True
        if isinstance(res, dict):
            self._server_capabilities = res.get("capabilities", {})
        await self.send_notification("initialized", {})
        return res

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
        await self.send_notification("textDocument/didOpen", params)

    async def shutdown(self):
        """Gracefully shuts down LSP server and cancels reader loop."""
        if self.initialized and self.process and self.process.returncode is None:
            try:
                await self.send_request("shutdown", None, timeout_sec=2.0)
                await self.send_notification("exit", None)
            except Exception:
                pass
            self.initialized = False

        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception:
                pass
            self.process = None

        # Clean up any pending futures
        for fut in self._pending_requests.values():
            if not fut.done():
                fut.set_exception(LSPUnavailableError("LSP server was shut down."))
        self._pending_requests.clear()

"""Unit tests for Async LSP Client with real JSON-RPC protocol execution."""

import sys

import pytest

from anvil.lsp_client import AsyncLSPClient, LSPError, LSPUnavailableError

# A minimal compliant JSON-RPC language server script for testing
MOCK_LSP_SERVER_SCRIPT = """
import sys
import json

def read_message():
    content_length = None
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
    if content_length is None:
        return None
    data = sys.stdin.read(content_length)
    return json.loads(data)

def send_message(msg):
    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\\r\\n\\r\\n".encode("ascii")
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()

while True:
    msg = read_message()
    if msg is None:
        break
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        send_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "capabilities": {
                    "hoverProvider": True,
                    "textDocumentSync": 1
                }
            }
        })
    elif method == "textDocument/hover":
        send_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"contents": "Hover documentation"}
        })
    elif method == "trigger_error":
        send_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32600, "message": "Invalid Request"}
        })
    elif method == "shutdown":
        send_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": None
        })
    elif method == "exit":
        break
"""


@pytest.mark.anyio
async def test_lsp_client_real_jsonrpc_lifecycle(tmp_path):
    server_script = tmp_path / "mock_server.py"
    server_script.write_text(MOCK_LSP_SERVER_SCRIPT, encoding="utf-8")

    client = AsyncLSPClient(
        server_command=[sys.executable, str(server_script)],
        root_uri="file:///workspace",
    )
    await client.start()

    # 1. Initialize
    init_res = await client.initialize()
    assert client.initialized is True
    assert init_res["capabilities"]["hoverProvider"] is True

    # 2. Open Document Notification
    await client.did_open("file:///workspace/main.py", "python", "x = 10")

    # 3. Custom Request (Hover)
    hover_res = await client.send_request("textDocument/hover", {"position": {"line": 0, "character": 1}})
    assert hover_res["contents"] == "Hover documentation"

    # 4. Error response decoding
    with pytest.raises(LSPError, match="Invalid Request"):
        await client.send_request("trigger_error", {})

    # 5. Shutdown
    await client.shutdown()
    assert client.initialized is False


@pytest.mark.anyio
async def test_lsp_client_unavailable_error():
    client = AsyncLSPClient(
        server_command=["nonexistent_language_server_binary_xyz"],
        root_uri="file:///workspace",
    )
    with pytest.raises(LSPUnavailableError):
        await client.start()

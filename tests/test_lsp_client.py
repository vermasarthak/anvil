"""Unit tests for Async LSP Client."""

import pytest

from anvil.lsp_client import AsyncLSPClient


@pytest.mark.anyio
async def test_lsp_client_lifecycle():
    client = AsyncLSPClient(server_command=["echo"], root_uri="file:///workspace")
    await client.start()

    init_res = await client.initialize()
    assert init_res["result"]["status"] == "ok"
    assert client.initialized is True

    await client.did_open("file:///workspace/main.py", "python", "print('hello')")
    await client.shutdown()
    assert client.initialized is False

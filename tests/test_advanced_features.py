import pytest

from anvil.daemon_supervisor import LSPDaemonSupervisor
from anvil.incremental_parser import TreeSitterIncrementalParser


@pytest.mark.anyio
async def test_lsp_daemon_supervisor():
    sup = LSPDaemonSupervisor()
    cmd = sup.discover_daemon("python")
    # Discovery returns list or None depending on environment
    assert cmd is None or isinstance(cmd, list)

    is_alive = await sup.check_health("python")
    assert is_alive is False

    status = await sup.restart_if_dead("non_existent_lang")
    assert status.is_running is False


def test_incremental_parser():
    parser = TreeSitterIncrementalParser("python")
    res = parser.parse_incremental("x = 1\ny = 2\n")
    assert res["status"] == "valid"
    assert res["ast_nodes"] == 2

    res_err = parser.parse_incremental("x = \n")
    assert res_err["status"] == "syntax_error"

"""Unit tests for gVisor Container Sandbox Security and Boundaries."""

import pytest

from anvil.sandbox import GVisorSandbox, SandboxConfig, SandboxSecurityError, SandboxUnavailableError


def test_gvisor_docker_cmd_construction(tmp_path):
    ws = tmp_path / "work"
    ws.mkdir()

    cfg = SandboxConfig(
        runtime="runsc",
        memory_limit_mb=256,
        cpu_quota=0.5,
        pids_limit=32,
        network_enabled=False,
        read_only_root=True,
        workspace_dir=str(ws),
        allowed_host_root=str(tmp_path),
    )
    sandbox = GVisorSandbox(cfg)
    docker_cmd = sandbox.build_docker_cmd(["python", "-c", "print(1)"])

    assert "--runtime=runsc" in docker_cmd
    assert "--memory=256m" in docker_cmd
    assert "--cpus=0.5" in docker_cmd
    assert "--pids-limit=32" in docker_cmd
    assert "--network=none" in docker_cmd
    assert "--read-only" in docker_cmd
    assert "-v" in docker_cmd
    assert f"{ws.resolve()}:/workspace:rw" in docker_cmd


def test_sandbox_path_traversal_rejection(tmp_path):
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    outside_dir = tmp_path / "secret"
    outside_dir.mkdir()

    cfg = SandboxConfig(
        workspace_dir=str(allowed_dir),
        allowed_host_root=str(allowed_dir),
    )
    sandbox = GVisorSandbox(cfg)

    # Attempt to point to directory outside allowed root
    with pytest.raises(SandboxSecurityError, match="traverses outside allowed host root"):
        sandbox.build_docker_cmd(["ls"], host_workspace=str(outside_dir))


def test_sandbox_symlink_escape_rejection(tmp_path):
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    outside_target = tmp_path / "secret_target"
    outside_target.mkdir()

    # Create symlink inside allowed pointing outside
    symlink_path = allowed_dir / "link_escape"
    symlink_path.symlink_to(outside_target)

    cfg = SandboxConfig(
        workspace_dir=str(allowed_dir),
        allowed_host_root=str(allowed_dir),
    )
    sandbox = GVisorSandbox(cfg)

    with pytest.raises(SandboxSecurityError):
        sandbox.build_docker_cmd(["ls"], host_workspace=str(symlink_path))


def test_sandbox_default_deny_when_runtime_unavailable(tmp_path):
    ws = tmp_path / "work"
    ws.mkdir()

    # Configure a non-existent container engine binary
    cfg = SandboxConfig(
        container_engine="nonexistent_container_engine_binary_xyz",
        workspace_dir=str(ws),
    )
    sandbox = GVisorSandbox(cfg)

    # Must raise SandboxUnavailableError and NEVER fall back to host execution
    with pytest.raises(SandboxUnavailableError, match="Default-deny: silent host execution fallback is prohibited"):
        sandbox.run_command(["echo", "should not execute on host"])

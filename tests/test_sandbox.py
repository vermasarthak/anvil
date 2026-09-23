"""Unit tests for gVisor Container Sandbox Wrapper."""

from anvil.sandbox import GVisorSandbox, SandboxConfig


def test_gvisor_docker_cmd_construction():
    cfg = SandboxConfig(
        runtime="runsc",
        memory_limit_mb=256,
        cpu_quota=0.5,
        network_enabled=False,
        read_only_root=True,
        workspace_dir="/tmp/work",
    )
    sandbox = GVisorSandbox(cfg)
    docker_cmd = sandbox.build_docker_cmd(["python", "-c", "print(1)"])

    assert "--runtime=runsc" in docker_cmd
    assert "--memory=256m" in docker_cmd
    assert "--cpus=0.5" in docker_cmd
    assert "--network=none" in docker_cmd
    assert "--read-only" in docker_cmd
    assert "-v" in docker_cmd
    assert "/tmp/work:/workspace" in docker_cmd


def test_sandbox_run_command_success():
    sandbox = GVisorSandbox()
    res = sandbox.run_command(["echo", "hello sandbox"])

    assert res.exit_code == 0
    assert "hello sandbox" in res.stdout
    assert res.duration_ms > 0.0

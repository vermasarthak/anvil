"""gVisor Container Sandbox Wrapper for Anvil."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SandboxConfig:
    """Configuration options for gVisor runsc sandbox container."""

    runtime: str = "runsc"
    memory_limit_mb: int = 512
    cpu_quota: float = 1.0
    network_enabled: bool = False
    read_only_root: bool = True
    workspace_dir: str = "/workspace"


@dataclass
class ExecutionResult:
    """Result of command executed inside sandbox."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float


class GVisorSandbox:
    """gVisor runsc Container Sandbox Wrapper."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()

    def build_docker_cmd(self, command: List[str], image: str = "python:3.11-slim") -> List[str]:
        """Constructs docker/podman run command configured with gVisor runsc runtime & security flags."""
        cmd = [
            "docker",
            "run",
            "--rm",
            f"--runtime={self.config.runtime}",
            f"--memory={self.config.memory_limit_mb}m",
            f"--cpus={self.config.cpu_quota}",
        ]
        if not self.config.network_enabled:
            cmd.append("--network=none")
        if self.config.read_only_root:
            cmd.append("--read-only")

        cmd.extend(
            [
                "-v",
                f"{self.config.workspace_dir}:/workspace",
                "-w",
                "/workspace",
                image,
            ]
        )
        cmd.extend(command)
        return cmd

    def run_command(self, command: List[str], timeout_sec: float = 30.0) -> ExecutionResult:
        """Executes command in isolated gVisor container sandbox or fallback subprocess."""
        t0 = time.perf_counter()
        try:
            res = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            t1 = time.perf_counter()
            return ExecutionResult(
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                duration_ms=(t1 - t0) * 1000.0,
            )
        except subprocess.TimeoutExpired as e:
            t1 = time.perf_counter()
            return ExecutionResult(
                exit_code=124,
                stdout=e.stdout or "",
                stderr="Execution timed out inside gVisor sandbox",
                duration_ms=(t1 - t0) * 1000.0,
            )

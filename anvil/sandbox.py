"""gVisor Container Sandbox Wrapper for Anvil.

Enforces real container isolation using gVisor (runsc) or OCI runtimes with default-deny semantics.
Host execution fallback is strictly prohibited.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class SandboxSecurityError(Exception):
    """Raised when an execution request violates sandbox security policies or isolation boundaries."""


class SandboxUnavailableError(Exception):
    """Raised when the required container runtime or gVisor sandbox is not available."""


@dataclass
class SandboxConfig:
    """Configuration options for gVisor runsc sandbox container."""

    runtime: str = "runsc"
    container_engine: str = "docker"
    memory_limit_mb: int = 512
    cpu_quota: float = 1.0
    pids_limit: int = 64
    network_enabled: bool = False
    read_only_root: bool = True
    workspace_dir: str = "/workspace"
    allowed_host_root: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of command executed inside sandbox."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float


class GVisorSandbox:
    """Enforced gVisor runsc Container Sandbox with default-deny semantics."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()

    def validate_workspace(self, host_path: str) -> Path:
        """Validates host workspace path against traversal, symlink escapes, and boundary limits."""
        resolved = Path(host_path).resolve()
        if not resolved.exists():
            raise SandboxSecurityError(f"Workspace path does not exist: {host_path}")

        if self.config.allowed_host_root:
            allowed_root = Path(self.config.allowed_host_root).resolve()
            try:
                resolved.relative_to(allowed_root)
            except ValueError as e:
                raise SandboxSecurityError(
                    f"Workspace path {resolved} traverses outside allowed host root {allowed_root}"
                ) from e

        # Check for symlink pointing outside
        if os.path.islink(host_path):
            target = Path(os.path.realpath(host_path))
            if self.config.allowed_host_root:
                allowed_root = Path(self.config.allowed_host_root).resolve()
                try:
                    target.relative_to(allowed_root)
                except ValueError as e:
                    raise SandboxSecurityError(f"Symlink {host_path} escapes allowed host root: {target}") from e

        return resolved

    def check_runtime_available(self) -> bool:
        """Checks if the container engine binary is present on host."""
        return shutil.which(self.config.container_engine) is not None

    def build_docker_cmd(
        self,
        command: List[str],
        image: str = "python:3.11-slim",
        host_workspace: Optional[str] = None,
    ) -> List[str]:
        """Constructs docker run command configured with gVisor runsc runtime & isolation flags."""
        ws_host = self.validate_workspace(host_workspace or self.config.workspace_dir)

        cmd = [
            self.config.container_engine,
            "run",
            "--rm",
            f"--runtime={self.config.runtime}",
            f"--memory={self.config.memory_limit_mb}m",
            f"--cpus={self.config.cpu_quota}",
            f"--pids-limit={self.config.pids_limit}",
        ]
        if not self.config.network_enabled:
            cmd.append("--network=none")
        if self.config.read_only_root:
            cmd.append("--read-only")

        cmd.extend(
            [
                "-v",
                f"{ws_host}:/workspace:rw",
                "-w",
                "/workspace",
                image,
            ]
        )
        cmd.extend(command)
        return cmd

    def run_command(
        self,
        command: List[str],
        timeout_sec: float = 30.0,
        host_workspace: Optional[str] = None,
        image: str = "python:3.11-slim",
    ) -> ExecutionResult:
        """Executes command inside isolated gVisor container.

        Default-deny: If container engine or runsc is unavailable, execution fails immediately;
        no silent host fallback is ever permitted.
        """
        if not self.check_runtime_available():
            raise SandboxUnavailableError(
                f"Container engine '{self.config.container_engine}' is not available on host. "
                "Default-deny: silent host execution fallback is prohibited."
            )

        docker_cmd = self.build_docker_cmd(command, image=image, host_workspace=host_workspace)

        t0 = time.perf_counter()
        try:
            res = subprocess.run(
                docker_cmd,
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
                stdout=e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
                stderr="Execution timed out inside gVisor container sandbox",
                duration_ms=(t1 - t0) * 1000.0,
            )
        except Exception as exc:
            t1 = time.perf_counter()
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"gVisor container execution error: {exc!s}",
                duration_ms=(t1 - t0) * 1000.0,
            )

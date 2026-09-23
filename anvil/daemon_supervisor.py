"""LSP Daemon Lifecycle Manager & Process Supervisor.

Handles binary discovery (pyright-langserver, gopls, rust-analyzer),
background spawning, health monitoring, and crash recovery.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DaemonStatus:
    name: str
    command: List[str]
    is_installed: bool
    is_running: bool
    pid: Optional[int] = None


class LSPDaemonSupervisor:
    """Manages language server daemon lifecycles across workspaces."""

    KNOWN_DAEMONS = {
        "python": ["pyright-langserver", "--stdio"],
        "go": ["gopls"],
        "rust": ["rust-analyzer"],
    }

    def __init__(self):
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}

    def discover_daemon(self, language: str) -> Optional[List[str]]:
        """Discovers binary on system PATH."""
        if language not in self.KNOWN_DAEMONS:
            return None
        cmd = self.KNOWN_DAEMONS[language]
        binary_path = shutil.which(cmd[0])
        if binary_path is None:
            return None
        return [binary_path] + cmd[1:]

    async def spawn_daemon(self, language: str) -> DaemonStatus:
        """Spawns background language server daemon with crash recovery."""
        cmd = self.discover_daemon(language)
        if not cmd:
            return DaemonStatus(name=language, command=[], is_installed=False, is_running=False)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.active_processes[language] = proc
            return DaemonStatus(name=language, command=cmd, is_installed=True, is_running=True, pid=proc.pid)
        except Exception:
            return DaemonStatus(name=language, command=cmd, is_installed=True, is_running=False)

    async def check_health(self, language: str) -> bool:
        """Checks if process is still responsive."""
        proc = self.active_processes.get(language)
        if proc is None:
            return False
        return proc.returncode is None

    async def restart_if_dead(self, language: str) -> DaemonStatus:
        """Restarts language server daemon if crashed."""
        is_alive = await self.check_health(language)
        if not is_alive:
            return await self.spawn_daemon(language)
        proc = self.active_processes[language]
        cmd = self.discover_daemon(language) or []
        return DaemonStatus(name=language, command=cmd, is_installed=True, is_running=True, pid=proc.pid)

    async def shutdown_all(self):
        """Terminates all active language server processes."""
        for proc in self.active_processes.values():
            try:
                proc.terminate()
                await proc.wait()
            except Exception:
                pass
        self.active_processes.clear()

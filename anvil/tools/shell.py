import asyncio
import os
from typing import Optional
from anvil.tools.base import BaseTool, ToolResult

class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Execute a shell command with a timeout in the local sandbox workspace."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command line to run."},
            "cwd": {"type": "string", "description": "Optional working directory for execution."},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)."}
        },
        "required": ["command"]
    }

    async def execute(self, command: str, cwd: Optional[str] = None, timeout: int = 60) -> ToolResult:
        try:
            target_cwd = cwd or os.getcwd()
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_cwd
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(timeout))
                out_str = stdout.decode("utf-8", errors="replace")
                err_str = stderr.decode("utf-8", errors="replace")
                combined = f"{out_str}\n{err_str}".strip()
                if proc.returncode == 0:
                    return ToolResult(success=True, output=combined)
                else:
                    return ToolResult(success=False, output=combined, error=f"Exit code {proc.returncode}")
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(success=False, output="", error=f"Command timed out after {timeout} seconds")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

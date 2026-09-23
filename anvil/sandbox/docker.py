import asyncio

from anvil.tools.base import ToolResult


class DockerSandbox:
    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image

    async def run_command(self, command: str, cwd: str, timeout: int = 60) -> ToolResult:
        docker_cmd = f'docker run --rm -v "{cwd}:/workspace" -w /workspace {self.image} sh -c "{command}"'
        try:
            proc = await asyncio.create_subprocess_shell(
                docker_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(timeout))
            out_str = stdout.decode("utf-8", errors="replace")
            err_str = stderr.decode("utf-8", errors="replace")
            combined = f"{out_str}\n{err_str}".strip()

            if proc.returncode == 0:
                return ToolResult(success=True, output=combined)
            else:
                return ToolResult(success=False, output=combined, error=f"Container exited with code {proc.returncode}")
        except asyncio.TimeoutError:
            return ToolResult(success=False, output="", error=f"Container execution timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

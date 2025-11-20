import os
from typing import Optional
from sol.tools.base import BaseTool, ToolResult

class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "Inspect unstaged and staged git changes in the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "staged": {"type": "boolean", "description": "Set true to inspect staged diffs."}
        },
        "required": []
    }

    async def execute(self, staged: bool = False) -> ToolResult:
        try:
            cmd = "git diff --staged" if staged else "git diff"
            proc = await os.system(cmd)
            # Use popen to capture output
            stream = os.popen(cmd)
            diff_text = stream.read()
            stream.close()
            
            if not diff_text.strip():
                return ToolResult(success=True, output="No active git diff changes.")
            return ToolResult(success=True, output=diff_text)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

class GitCommitTool(BaseTool):
    name = "git_commit"
    description = "Stage changes and create an atomic git commit."
    parameters = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Commit message describing the changes."}
        },
        "required": ["message"]
    }

    async def execute(self, message: str) -> ToolResult:
        try:
            os.system("git add -A")
            stream = os.popen(f'git commit -m "{message}"')
            out = stream.read()
            stream.close()
            return ToolResult(success=True, output=out or "Commit created successfully.")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

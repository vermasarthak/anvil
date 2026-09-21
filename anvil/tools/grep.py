import os
from typing import List, Dict, Any, Optional
from anvil.tools.base import BaseTool, ToolResult

class GrepTool(BaseTool):
    name = "grep"
    description = "Perform fast regex pattern search across repository files."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Regex or substring query."},
            "path": {"type": "string", "description": "Subdirectory path filter."}
        },
        "required": ["query"]
    }

    async def execute(self, query: str, path: Optional[str] = None) -> ToolResult:
        try:
            target = path or "."
            matches = []
            for root, _, files in os.walk(target):
                if ".git" in root or ".venv" in root or "node_modules" in root:
                    continue
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            for idx, line in enumerate(f):
                                if query in line:
                                    matches.append(f"{filepath}:{idx + 1}: {line.strip()}")
                                    if len(matches) >= 50:
                                        break
                    except Exception:
                        pass
                if len(matches) >= 50:
                    break

            if not matches:
                return ToolResult(success=True, output=f"No grep matches found for '{query}'.")
            return ToolResult(success=True, output="\n".join(matches))
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

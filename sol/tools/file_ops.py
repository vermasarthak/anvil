import os
import glob
from typing import Optional
from sol.tools.base import BaseTool, ToolResult

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read file contents with optional line range selection."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative or absolute path to the target file."},
            "start_line": {"type": "integer", "description": "Optional 1-indexed starting line number."},
            "end_line": {"type": "integer", "description": "Optional 1-indexed ending line number."}
        },
        "required": ["path"]
    }

    async def execute(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> ToolResult:
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, output="", error=f"File not found: {path}")
            
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                
            if start_line is not None or end_line is not None:
                start = (start_line - 1) if start_line and start_line > 0 else 0
                end = end_line if end_line else len(lines)
                selected = lines[start:end]
                content = "".join([f"{i + start + 1}: {line}" for i, line in enumerate(selected)])
            else:
                content = "".join([f"{i + 1}: {line}" for i, line in enumerate(lines)])
                
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Perform a exact search-and-replace edit on a file."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the target file."},
            "old_string": {"type": "string", "description": "The target string to replace."},
            "new_string": {"type": "string", "description": "The replacement string."}
        },
        "required": ["path", "old_string", "new_string"]
    }

    async def execute(self, path: str, old_string: str, new_string: str) -> ToolResult:
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, output="", error=f"File not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            if old_string not in content:
                return ToolResult(success=False, output="", error="Target 'old_string' not found in file.")
                
            updated = content.replace(old_string, new_string, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(updated)
                
            return ToolResult(success=True, output=f"Successfully edited {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create a new file with the specified code or text content."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to create."},
            "content": {"type": "string", "description": "Initial content to write to the file."}
        },
        "required": ["path", "content"]
    }

    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(success=True, output=f"Successfully created {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

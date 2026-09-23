import abc
from typing import Any, Dict, Optional


class ToolResult:
    def __init__(self, success: bool, output: str, error: Optional[str] = None):
        self.success = success
        self.output = output
        self.error = error


class BaseTool(abc.ABC):
    name: str
    description: str
    parameters: Dict[str, Any]

    @abc.abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass

    def to_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

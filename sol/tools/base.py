import abc
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None

class BaseTool(abc.ABC):
    name: str
    description: str
    parameters: Dict[str, Any]

    @abc.abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass

    def to_schema((self)) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

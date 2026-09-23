from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    output: str
    error: Optional[str] = None


class AgentMessage(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class LLMResponse(BaseModel):
    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    raw_response: Optional[Any] = None

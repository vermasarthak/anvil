import json
import httpx
from typing import List, Dict, Any, Optional
from sol.llm.base import BaseLLMProvider
from sol.llm.schema import AgentMessage, LLMResponse, ToolCall

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "qwen3-coder:14b", api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url or "http://localhost:11434")

    async def generate(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        ollama_messages = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments
                        }
                    }
                    for tc in msg.tool_calls
                ]
            ollama_messages.append(m)

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": {"temperature": temperature}
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                raise RuntimeError(f"Ollama API request failed: {str(e)}")

        msg_data = data.get("message", {})
        content = msg_data.get("content", "")
        tool_calls = []

        if "tool_calls" in msg_data and msg_data["tool_calls"]:
            for idx, tc in enumerate(msg_data["tool_calls"]):
                func = tc.get("function", {})
                tool_calls.append(
                    ToolCall(
                        id=f"call_{idx}",
                        name=func.get("name", ""),
                        arguments=func.get("arguments", {})
                    )
                )

        return LLMResponse(content=content, tool_calls=tool_calls, raw_response=data)

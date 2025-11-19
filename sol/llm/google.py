import os
import httpx
from typing import List, Dict, Any, Optional
from sol.llm.base import BaseLLMProvider
from sol.llm.schema import AgentMessage, LLMResponse, ToolCall

class GoogleProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None, base_url: Optional[str] = None):
        key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        super().__init__(model_name, key, base_url or "https://generativelanguage.googleapis.com/v1beta")

    async def generate(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY environment variable or configure in settings.")

        contents = []
        for msg in messages:
            role = "user" if msg.role in ["user", "system", "tool"] else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature}
        }

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
            except Exception as e:
                raise RuntimeError(f"Google Gemini API request failed: {str(e)}")

        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for p in parts:
                if "text" in p:
                    content += p["text"]

        return LLMResponse(content=content, tool_calls=[], raw_response=data)

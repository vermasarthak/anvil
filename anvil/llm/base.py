import abc
from typing import List, Dict, Any, Optional
from anvil.llm.schema import AgentMessage, LLMResponse

class BaseLLMProvider(abc.ABC):
    def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

    @abc.abstractmethod
    async def generate(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Generate response from the model."""
        pass

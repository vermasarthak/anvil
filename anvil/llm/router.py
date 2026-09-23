from typing import Dict, Optional, Type

from anvil.llm.base import BaseLLMProvider
from anvil.llm.google import GoogleProvider
from anvil.llm.ollama import OllamaProvider


class LLMRouter:
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "ollama": OllamaProvider,
        "google": GoogleProvider,
    }

    @classmethod
    def get_provider(
        cls,
        provider_name: str,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> BaseLLMProvider:
        provider_cls = cls._providers.get(provider_name.lower())
        if not provider_cls:
            raise ValueError(f"Unknown LLM provider '{provider_name}'. Supported: {list(cls._providers.keys())}")

        kwargs = {}
        if model_name:
            kwargs["model_name"] = model_name
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url

        return provider_cls(**kwargs)

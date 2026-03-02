"""
AgentForge - LLM Integration Module
Supports Ollama, OpenAI, and other LLM providers.
"""
import os
import json
import asyncio
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM provider"""
    
    @abstractmethod
    async def generate(self, prompt: str, context: Dict = None, **kwargs) -> str:
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
        self._available_models = None
    
    async def generate(self, prompt: str, context: Dict = None, **kwargs) -> str:
        """Generate response from Ollama"""
        import aiohttp
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": self._build_prompt(prompt, context),
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("response", "")
                    else:
                        return f"Error: {resp.status} - {await resp.text()}"
        except Exception as e:
            return f"Ollama Error: {str(e)}"
    
    async def chat(self, messages: list, **kwargs) -> str:
        """Chat with Ollama using messages format"""
        import aiohttp
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("message", {}).get("content", "")
                    else:
                        return f"Error: {resp.status}"
        except Exception as e:
            return f"Ollama Error: {str(e)}"
    
    async def list_models(self) -> list:
        """List available Ollama models"""
        import aiohttp
        
        if self._available_models:
            return self._available_models
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self._available_models = [m["name"] for m in result.get("models", [])]
                        return self._available_models
        except Exception:
            pass
        return []
    
    async def check_health(self) -> bool:
        """Check if Ollama is running"""
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception:
            return False
    
    def _build_prompt(self, prompt: str, context: Dict = None) -> str:
        """Build prompt with context"""
        if not context:
            return prompt
        
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"Context: {context_str}\n\nTask: {prompt}"


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
    
    async def generate(self, prompt: str, context: Dict = None, **kwargs) -> str:
        """Generate response from OpenAI"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": "\n".join([f"{k}: {v}" for k, v in context.items()])
            })
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}"


class LLMManager:
    """Central LLM management"""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = "ollama"
    
    def register_provider(self, name: str, provider: LLMProvider):
        self.providers[name] = provider
    
    def get_provider(self, name: str = None) -> LLMProvider:
        name = name or self.default_provider
        if name not in self.providers:
            # Auto-detect provider
            if name == "ollama":
                self.providers[name] = OllamaProvider()
            elif name == "openai":
                self.providers[name] = OpenAIProvider()
        return self.providers.get(name)
    
    async def generate(self, prompt: str, provider: str = None, **kwargs) -> str:
        """Generate using specified provider"""
        p = self.get_provider(provider)
        return await p.generate(prompt, **kwargs)
    
    async def chat(self, messages: list, provider: str = None, **kwargs) -> str:
        """Chat using specified provider"""
        p = self.get_provider(provider)
        if hasattr(p, 'chat'):
            return await p.chat(messages, **kwargs)
        # Fallback for providers without chat
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        return await p.generate(prompt, **kwargs)


# Global LLM manager
llm_manager = LLMManager()


# Convenience functions
async def generate_with_ollama(prompt: str, model: str = "llama3.2", **kwargs) -> str:
    """Quick Ollama generation"""
    provider = OllamaProvider(model=model)
    return await provider.generate(prompt, **kwargs)


async def chat_with_ollama(messages: list, model: str = "llama3.2") -> str:
    """Quick Ollama chat"""
    provider = OllamaProvider(model=model)
    return await provider.chat(messages)

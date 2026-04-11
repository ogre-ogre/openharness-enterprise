"""
OpenHarness Enterprise - LLM Client

LLM client that supports Anthropic and OpenAI-compatible APIs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator, Optional

from openharness.enterprise.config.provider import get_provider_config


class LLMClient:
    """
    LLM Client for streaming responses.
    
    Supports:
    - Anthropic API (official and compatible)
    - OpenAI-compatible APIs (百炼, 智谱, DeepSeek, etc.)
    - Skill loading and injection
    """
    
    def __init__(self):
        self.config = get_provider_config()
        self._client = None
        self._client_type = None  # 'anthropic' or 'openai'
    
    def _get_client(self):
        """Get or create LLM client."""
        if self._client is None:
            if not self.config.api_key:
                raise ValueError("API key not configured. Set OH_API_KEY environment variable.")
            
            provider = self.config.provider.lower()
            
            # 判断是 OpenAI 兼容还是 Anthropic
            if provider in ('openai', 'openai-compatible', 'bailian', 'zhipu', 'deepseek'):
                # 使用 OpenAI SDK
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url
                )
                self._client_type = 'openai'
                print(f"[LLM] Using OpenAI-compatible client: {self.config.base_url}")
            else:
                # 使用 Anthropic SDK
                from anthropic import AsyncAnthropic
                client_kwargs = {"api_key": self.config.api_key}
                if self.config.base_url:
                    client_kwargs["base_url"] = self.config.base_url
                self._client = AsyncAnthropic(**client_kwargs)
                self._client_type = 'anthropic'
                print(f"[LLM] Using Anthropic client: {self.config.base_url or 'default'}")
        
        return self._client
    
    def load_skill_content(self, skill_name: str, skills_base_path: str) -> Optional[str]:
        """Load skill content from file."""
        from openharness.enterprise.users.workspace import get_shared_root, get_enterprise_root
        
        # Try skills_base_path first (user's personal skills)
        skill_path = Path(skills_base_path) / skill_name / "SKILL.md"
        if skill_path.exists():
            try:
                return skill_path.read_text(encoding="utf-8")
            except Exception:
                pass
        
        # Try shared skills directory
        skill_path = get_shared_root() / "skills" / skill_name / "SKILL.md"
        if skill_path.exists():
            try:
                return skill_path.read_text(encoding="utf-8")
            except Exception:
                pass
        
        return None
    
    def build_system_prompt(
        self,
        base_prompt: Optional[str] = None,
        skills: Optional[List[str]] = None,
        skills_base_path: Optional[str] = None
    ) -> str:
        """
        Build system prompt with optional skills.
        
        Args:
            base_prompt: Base system prompt (user's soul)
            skills: List of skill names to load
            skills_base_path: Base path to search for skills
        
        Returns:
            Complete system prompt
        """
        parts = []
        
        # Add base prompt (user's soul)
        if base_prompt:
            parts.append(base_prompt)
        
        # Add skills
        if skills:
            for skill_name in skills:
                skill_content = None
                
                # Try shared skills directory first
                if skills_base_path:
                    skill_content = self.load_skill_content(skill_name, skills_base_path)
                
                # Try shared skills in default location
                if not skill_content:
                    from openharness.enterprise.users.workspace import get_shared_root
                    skill_content = self.load_skill_content(skill_name, str(get_shared_root() / "skills"))
                
                if skill_content:
                    parts.append(f"\n\n---\n## Skill: {skill_name}\n\n{skill_content}")
        
        return "\n\n".join(parts) if parts else "You are a helpful AI assistant."
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        skills: Optional[List[str]] = None,
        skills_base_path: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response.
        
        Args:
            messages: Chat messages in format [{"role": "user/assistant", "content": "..."}]
            system_prompt: Base system prompt (user's soul)
            skills: List of skill names to load and inject
            skills_base_path: Base path to search for skills
        
        Yields:
            Text chunks
        """
        client = self._get_client()
        
        # Build complete system prompt with skills
        full_system_prompt = self.build_system_prompt(system_prompt, skills, skills_base_path)
        
        # Convert messages to proper format
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                formatted_messages.append({"role": role, "content": content})
        
        try:
            if self._client_type == 'openai':
                # OpenAI-compatible API
                print(f"[LLM] Calling OpenAI-compatible API: {self.config.model}")
                print(f"[LLM] Messages: {len(formatted_messages)}, System prompt length: {len(full_system_prompt)}")
                
                api_kwargs = {
                    "model": self.config.model,
                    "messages": formatted_messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "stream": True,
                }
                
                # 添加 system message（OpenAI 格式）
                if full_system_prompt:
                    api_kwargs["messages"] = [
                        {"role": "system", "content": full_system_prompt}
                    ] + api_kwargs["messages"]
                
                stream = await client.chat.completions.create(**api_kwargs)
                
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            else:
                # Anthropic API
                print(f"[LLM] Calling Anthropic API: {self.config.model}")
                print(f"[LLM] Messages: {len(formatted_messages)}, System prompt length: {len(full_system_prompt)}")
                
                api_kwargs = {
                    "model": self.config.model,
                    "max_tokens": self.config.max_tokens,
                    "messages": formatted_messages,
                    "system": full_system_prompt,
                }
                
                async with client.messages.stream(**api_kwargs) as stream:
                    async for text in stream.text_stream:
                        yield text
                    
        except Exception as e:
            print(f"[LLM] Error: {e}")
            raise RuntimeError(f"LLM API error: {e}")


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
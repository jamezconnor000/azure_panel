"""
Aether Familiar - Core Agent
Minimal Claude agent with tool execution for panel development.
"""

import os
import json
import asyncio
from typing import AsyncGenerator, Optional, List, Dict, Any
from pathlib import Path

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from .tools import TOOLS, execute_tool

# Load system prompt
FAMILIAR_DIR = Path(__file__).parent
SYSTEM_PROMPT_PATH = FAMILIAR_DIR / "FAMILIAR.md"

def load_system_prompt() -> str:
    """Load the Familiar system prompt."""
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text()
    return DEFAULT_SYSTEM_PROMPT

DEFAULT_SYSTEM_PROMPT = """You are Aether Familiar, an AI development assistant embedded in an Azure BLU-IC2 access control panel.

You have direct access to:
- Aether Thrall (HAL) - Hardware abstraction, AetherDB
- Aether Bifrost (API) - External API, sync status
- Aether Saga (Web UI) - Frontend files
- System - Logs, processes, commands

You help the developer build, debug, and refine the Aether Access system.

Be concise. You're running on embedded hardware - minimize token usage.
Execute tools to gather information before answering.
When editing files, make minimal targeted changes."""


class AetherFamiliar:
    """
    Ultra-lightweight Claude agent for panel development.

    Features:
    - Tool execution for panel operations
    - Conversation history management
    - Streaming responses
    - Minimal resource footprint
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ):
        if not HAS_ANTHROPIC:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = load_system_prompt()
        self.history: List[Dict[str, Any]] = []

    def clear_history(self):
        """Clear conversation history."""
        self.history = []

    async def chat(self, message: str) -> str:
        """
        Send a message and get a response.
        Handles tool calls automatically.
        """
        # Add user message to history
        self.history.append({"role": "user", "content": message})

        # Initial API call
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            tools=TOOLS,
            messages=self.history
        )

        # Handle tool use loop
        while response.stop_reason == "tool_use":
            # Extract and execute tools
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use":
                    try:
                        result = await execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

            # Add assistant response and tool results to history
            self.history.append({"role": "assistant", "content": assistant_content})
            self.history.append({"role": "user", "content": tool_results})

            # Continue conversation
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=TOOLS,
                messages=self.history
            )

        # Extract final text response
        final_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text

        # Add final response to history
        self.history.append({"role": "assistant", "content": response.content})

        # Trim history if too long (keep last 20 exchanges)
        if len(self.history) > 40:
            self.history = self.history[-40:]

        return final_text

    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Stream a response token by token.
        Note: Tool calls are executed before streaming final response.
        """
        # Add user message
        self.history.append({"role": "user", "content": message})

        # Initial call (non-streaming to handle tools)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            tools=TOOLS,
            messages=self.history
        )

        # Handle tool use (non-streaming)
        while response.stop_reason == "tool_use":
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use":
                    yield f"[Executing: {block.name}]\n"
                    try:
                        result = await execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

            self.history.append({"role": "assistant", "content": assistant_content})
            self.history.append({"role": "user", "content": tool_results})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=TOOLS,
                messages=self.history
            )

        # Stream final response
        final_content = response.content
        self.history.append({"role": "assistant", "content": final_content})

        for block in final_content:
            if hasattr(block, "text"):
                yield block.text

        # Trim history
        if len(self.history) > 40:
            self.history = self.history[-40:]


# Singleton instance for simple usage
_familiar: Optional[AetherFamiliar] = None

def get_familiar() -> AetherFamiliar:
    """Get or create the global Familiar instance."""
    global _familiar
    if _familiar is None:
        _familiar = AetherFamiliar()
    return _familiar

async def chat(message: str) -> str:
    """Simple chat function using global instance."""
    return await get_familiar().chat(message)

async def chat_stream(message: str) -> AsyncGenerator[str, None]:
    """Simple streaming chat using global instance."""
    async for chunk in get_familiar().chat_stream(message):
        yield chunk

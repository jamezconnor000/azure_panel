"""
Aether Familiar - Embedded AI Development Assistant
Ultra-lightweight Claude agent for Azure BLU-IC2 panels.
"""

from .agent import AetherFamiliar, chat, chat_stream
from .tools import TOOLS

__version__ = "1.0.0"
__all__ = ["AetherFamiliar", "chat", "chat_stream", "TOOLS"]

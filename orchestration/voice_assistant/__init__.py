"""
Voice Assistant Orchestration Module

This module provides:
- Cloud-based speech-to-text (OpenAI Whisper, Azure Speech)
- Intent classification and routing
- Integration with existing orchestrations (commit, GitHub-LLM, general)
- Voice-optimized response formatting
- Text-to-speech synthesis
"""

from .voice_orchestrator import VoiceOrchestrator
from .session_manager import SessionManager
from .intent_classifier import IntentClassifier
from .response_formatter import VoiceResponseFormatter

__all__ = [
    "VoiceOrchestrator",
    "SessionManager",
    "IntentClassifier",
    "VoiceResponseFormatter",
]

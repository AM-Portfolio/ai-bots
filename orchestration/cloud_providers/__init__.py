"""
Cloud Provider Abstraction Layer

This package provides cloud-agnostic interfaces for AI services,
enabling easy switching between providers (Azure, Together AI, OpenAI, etc.)
"""

from .templates.base import (
    CloudProvider,
    STTProvider,
    TTSProvider,
    TranslationProvider,
    LLMProvider,
    ProviderCapability
)

__all__ = [
    'CloudProvider',
    'STTProvider',
    'TTSProvider',
    'TranslationProvider',
    'LLMProvider',
    'ProviderCapability'
]

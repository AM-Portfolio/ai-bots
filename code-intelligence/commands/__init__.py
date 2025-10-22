"""Command handlers for CLI"""

from .handlers import (
    handle_embed,
    handle_summarize,
    handle_analyze,
    handle_repo_analyze,
    handle_health,
    handle_test,
)

__all__ = [
    "handle_embed",
    "handle_summarize",
    "handle_analyze",
    "handle_repo_analyze",
    "handle_health",
    "handle_test",
]

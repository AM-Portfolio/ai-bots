"""
Command handlers for code-intelligence CLI.
"""

from .cmd_embed import cmd_embed
from .cmd_summarize import cmd_summarize
from .cmd_analyze import cmd_analyze
from .cmd_repo_analyze import cmd_repo_analyze
from .cmd_health import cmd_health
from .cmd_test import cmd_test

__all__ = [
    "cmd_embed",
    "cmd_summarize",
    "cmd_analyze",
    "cmd_repo_analyze",
    "cmd_health",
    "cmd_test"
]

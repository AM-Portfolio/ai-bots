"""
Summary/Beautify Layer

Formats and enhances responses for optimal LLM consumption.
"""

from .beautifier import ResponseBeautifier
from .formatters import MarkdownFormatter, JSONFormatter, PlainTextFormatter

__all__ = ['ResponseBeautifier', 'MarkdownFormatter', 'JSONFormatter', 'PlainTextFormatter']

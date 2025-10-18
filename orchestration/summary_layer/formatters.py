"""
Response Formatters

Different formatting strategies for responses.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json


class ResponseFormatter(ABC):
    """Base class for response formatters"""
    
    @abstractmethod
    def format(self, content: Dict[str, Any]) -> str:
        """Format content"""
        pass


class MarkdownFormatter(ResponseFormatter):
    """Format responses as Markdown"""
    
    def format(self, content: Dict[str, Any]) -> str:
        """Format as Markdown"""
        markdown = f"# {content.get('title', 'Response')}\n\n"
        
        if 'summary' in content:
            markdown += f"{content['summary']}\n\n"
        
        if 'sections' in content:
            for section in content['sections']:
                markdown += f"## {section.get('title', 'Section')}\n\n"
                markdown += f"{section.get('content', '')}\n\n"
        
        if 'code' in content:
            lang = content.get('language', '')
            markdown += f"```{lang}\n{content['code']}\n```\n\n"
        
        return markdown


class JSONFormatter(ResponseFormatter):
    """Format responses as JSON"""
    
    def format(self, content: Dict[str, Any]) -> str:
        """Format as pretty JSON"""
        return json.dumps(content, indent=2, ensure_ascii=False)


class PlainTextFormatter(ResponseFormatter):
    """Format responses as plain text"""
    
    def format(self, content: Dict[str, Any]) -> str:
        """Format as plain text"""
        text_parts = []
        
        if 'title' in content:
            text_parts.append(content['title'])
            text_parts.append("=" * len(content['title']))
        
        if 'summary' in content:
            text_parts.append(content['summary'])
        
        if 'sections' in content:
            for section in content['sections']:
                text_parts.append(f"\n{section.get('title', 'Section')}")
                text_parts.append("-" * len(section.get('title', 'Section')))
                text_parts.append(section.get('content', ''))
        
        return "\n\n".join(text_parts)

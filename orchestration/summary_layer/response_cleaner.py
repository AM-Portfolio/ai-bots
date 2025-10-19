"""
Response Cleaner Module
Cleans and formats LLM responses for proper alignment, spacing, and line breaks
"""

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class ResponseCleaner:
    """Cleans and formats LLM responses for better readability"""
    
    def __init__(self):
        logger.info("🧹 Response Cleaner initialized")
    
    def clean(self, text: str) -> str:
        """
        Clean and format response text
        
        Steps:
        1. Normalize line breaks
        2. Fix spacing around headers
        3. Fix list formatting
        4. Fix code block spacing
        5. Remove excessive whitespace
        6. Ensure proper paragraph spacing
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned and formatted text
        """
        if not text or not text.strip():
            return text
        
        logger.debug("🧹 Cleaning response text...")
        
        # Step 1: Normalize line breaks (CRLF -> LF)
        text = self._normalize_line_breaks(text)
        
        # Step 2: Fix spacing around headers
        text = self._fix_header_spacing(text)
        
        # Step 3: Fix list formatting
        text = self._fix_list_formatting(text)
        
        # Step 4: Fix code block spacing
        text = self._fix_code_blocks(text)
        
        # Step 5: Remove excessive whitespace
        text = self._remove_excessive_whitespace(text)
        
        # Step 6: Ensure proper paragraph spacing
        text = self._fix_paragraph_spacing(text)
        
        # Step 7: Trim final result
        text = text.strip()
        
        logger.debug("✅ Response text cleaned")
        return text
    
    def _normalize_line_breaks(self, text: str) -> str:
        """Normalize all line breaks to \n"""
        # Replace CRLF with LF
        text = text.replace('\r\n', '\n')
        # Replace CR with LF
        text = text.replace('\r', '\n')
        return text
    
    def _fix_header_spacing(self, text: str) -> str:
        """
        Ensure proper spacing around markdown headers
        - Empty line before header (except first line)
        - Empty line after header
        """
        lines = text.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            # Check if this is a header
            if re.match(r'^#+\s+', line):
                # Add empty line before header (if not at start and previous line isn't empty)
                if i > 0 and result and result[-1].strip():
                    result.append('')
                
                result.append(line)
                
                # Add empty line after header (if next line exists and isn't empty)
                if i < len(lines) - 1 and lines[i + 1].strip():
                    result.append('')
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _fix_list_formatting(self, text: str) -> str:
        """
        Fix list item spacing and alignment
        - Ensure consistent spacing in lists
        - Fix indentation for nested lists
        """
        lines = text.split('\n')
        result = []
        in_list = False
        
        for i, line in enumerate(lines):
            # Check if this is a list item
            is_list_item = bool(re.match(r'^\s*[-*+]\s+', line) or re.match(r'^\s*\d+\.\s+', line))
            
            if is_list_item:
                if not in_list and result and result[-1].strip():
                    # Add empty line before list starts
                    result.append('')
                in_list = True
                result.append(line)
            else:
                if in_list and line.strip():
                    # List ended, add empty line after
                    result.append('')
                    in_list = False
                result.append(line)
        
        return '\n'.join(result)
    
    def _fix_code_blocks(self, text: str) -> str:
        """
        Ensure proper spacing around code blocks
        - Empty line before ```
        - Empty line after closing ```
        """
        lines = text.split('\n')
        result = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Opening code block
                    if result and result[-1].strip():
                        result.append('')
                    in_code_block = True
                    result.append(line)
                else:
                    # Closing code block
                    result.append(line)
                    if i < len(lines) - 1 and lines[i + 1].strip():
                        result.append('')
                    in_code_block = False
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _remove_excessive_whitespace(self, text: str) -> str:
        """Remove more than 2 consecutive empty lines"""
        # Replace 3+ newlines with exactly 2 newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace from each line
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        
        return '\n'.join(lines)
    
    def _fix_paragraph_spacing(self, text: str) -> str:
        """
        Ensure proper paragraph spacing
        - Single empty line between paragraphs
        - No empty lines within paragraphs
        """
        # Split into paragraphs
        paragraphs = re.split(r'\n\n+', text)
        
        # Clean each paragraph (remove internal empty lines)
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # If it's a special block (code, list, header), preserve it
                if (para.startswith('#') or 
                    para.startswith('```') or 
                    any(line.strip().startswith(('- ', '* ', '+ ', '1.', '2.', '3.'))
                        for line in para.split('\n'))):
                    cleaned_paragraphs.append(para)
                else:
                    # Regular paragraph - join lines with single space
                    lines = para.split('\n')
                    # Don't join if lines are already well-formatted (bullet points, etc.)
                    if all(not line.strip().startswith(('-', '*', '+', '1.', '2.', '3.')) 
                           for line in lines):
                        para = ' '.join(line.strip() for line in lines if line.strip())
                    cleaned_paragraphs.append(para)
        
        # Join paragraphs with double newline
        return '\n\n'.join(cleaned_paragraphs)
    
    def clean_with_metadata(self, text: str) -> Tuple[str, dict]:
        """
        Clean text and return cleaning metadata
        
        Returns:
            Tuple of (cleaned_text, metadata)
        """
        original_lines = len(text.split('\n'))
        original_length = len(text)
        
        cleaned = self.clean(text)
        
        cleaned_lines = len(cleaned.split('\n'))
        cleaned_length = len(cleaned)
        
        metadata = {
            'original_lines': original_lines,
            'cleaned_lines': cleaned_lines,
            'original_length': original_length,
            'cleaned_length': cleaned_length,
            'reduction_percent': round(100 * (1 - cleaned_length / original_length), 2) if original_length > 0 else 0
        }
        
        logger.info(f"🧹 Cleaned response: {original_lines} -> {cleaned_lines} lines, "
                   f"{original_length} -> {cleaned_length} chars "
                   f"({metadata['reduction_percent']}% reduction)")
        
        return cleaned, metadata


# Global instance
response_cleaner = ResponseCleaner()

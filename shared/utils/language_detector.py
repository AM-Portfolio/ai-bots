"""
Language Detection Utility

Detects language (English vs Hindi) from text input.
Supports multilingual responses in Voice Assistant and Chat.
"""
import re
from typing import Literal, Tuple
from shared.config import settings

LanguageCode = Literal["en", "hi"]


class LanguageDetector:
    """Detects language from text using character ranges and patterns"""
    
    # Devanagari script Unicode range (used for Hindi)
    DEVANAGARI_RANGE = (0x0900, 0x097F)
    
    # Common Hindi words
    HINDI_WORDS = [
        "है", "हैं", "का", "की", "के", "में", "से", "को", "ने", 
        "पर", "यह", "वह", "कर", "दो", "एक", "क्या", "कैसे", "कहाँ"
    ]
    
    # Common English words
    ENGLISH_WORDS = [
        "the", "is", "are", "in", "on", "at", "to", "for", "of", "and",
        "a", "an", "this", "that", "what", "how", "where", "when"
    ]
    
    def __init__(self):
        self.enabled = settings.language_detection_enabled
        self.default_language = settings.default_language
    
    def detect(self, text: str) -> LanguageCode:
        """
        Detect language from text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code ('en' or 'hi')
        """
        if not self.enabled or not text:
            return self.default_language  # type: ignore
        
        text_lower = text.lower().strip()
        
        # Count Devanagari characters
        devanagari_count = sum(
            1 for char in text
            if self.DEVANAGARI_RANGE[0] <= ord(char) <= self.DEVANAGARI_RANGE[1]
        )
        
        # Calculate percentage of Devanagari characters
        total_chars = len([c for c in text if not c.isspace()])
        devanagari_percentage = (devanagari_count / total_chars * 100) if total_chars > 0 else 0
        
        # If >30% Devanagari characters, it's Hindi
        if devanagari_percentage > 30:
            return "hi"
        
        # Check for Hindi words
        hindi_word_count = sum(1 for word in self.HINDI_WORDS if word in text)
        
        # Check for English words
        english_word_count = sum(1 for word in self.ENGLISH_WORDS if word in text_lower)
        
        # Decide based on word matches
        if hindi_word_count > english_word_count:
            return "hi"
        elif english_word_count > 0:
            return "en"
        
        # Default fallback
        return self.default_language  # type: ignore
    
    def detect_with_confidence(self, text: str) -> Tuple[LanguageCode, float]:
        """
        Detect language with confidence score
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        if not self.enabled or not text:
            return self.default_language, 0.5  # type: ignore
        
        text_lower = text.lower().strip()
        total_chars = len([c for c in text if not c.isspace()])
        
        if total_chars == 0:
            return self.default_language, 0.5  # type: ignore
        
        # Count Devanagari characters
        devanagari_count = sum(
            1 for char in text
            if self.DEVANAGARI_RANGE[0] <= ord(char) <= self.DEVANAGARI_RANGE[1]
        )
        
        devanagari_percentage = (devanagari_count / total_chars * 100)
        
        # High confidence Hindi detection
        if devanagari_percentage > 50:
            return "hi", min(devanagari_percentage / 100, 1.0)
        
        # Check word matches
        hindi_word_count = sum(1 for word in self.HINDI_WORDS if word in text)
        english_word_count = sum(1 for word in self.ENGLISH_WORDS if word in text_lower)
        
        total_word_matches = hindi_word_count + english_word_count
        
        if total_word_matches > 0:
            if hindi_word_count > english_word_count:
                confidence = hindi_word_count / total_word_matches
                return "hi", confidence
            elif english_word_count > 0:
                confidence = english_word_count / total_word_matches
                return "en", confidence
        
        # Medium confidence based on Devanagari presence
        if devanagari_percentage > 10:
            return "hi", 0.6
        
        # Default to English with low confidence
        return "en", 0.5
    
    def get_language_instruction(self, detected_language: LanguageCode) -> str:
        """
        Get instruction to include in LLM prompt for language-specific response
        
        Args:
            detected_language: Detected language code
            
        Returns:
            Instruction string for LLM prompt
        """
        instructions = {
            "en": "Respond in English.",
            "hi": "Respond in Hindi (Devanagari script). Use natural, conversational Hindi."
        }
        return instructions.get(detected_language, instructions["en"])
    
    def get_language_name(self, code: LanguageCode) -> str:
        """Get human-readable language name"""
        names = {
            "en": "English",
            "hi": "Hindi"
        }
        return names.get(code, "English")


# Global instance
_language_detector = LanguageDetector()


def detect_language(text: str) -> LanguageCode:
    """Detect language from text (convenience function)"""
    return _language_detector.detect(text)


def detect_language_with_confidence(text: str) -> Tuple[LanguageCode, float]:
    """Detect language with confidence score (convenience function)"""
    return _language_detector.detect_with_confidence(text)


def get_language_instruction(detected_language: LanguageCode) -> str:
    """Get LLM instruction for language-specific response (convenience function)"""
    return _language_detector.get_language_instruction(detected_language)

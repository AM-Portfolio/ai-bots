"""
Logging Configuration for Code Intelligence

Provides granular control over logging levels for different components.
"""

import logging
import sys
from typing import Optional, Dict


class CodeIntelligenceLogger:
    """Configure logging for code intelligence components"""
    
    # Default log levels for different components
    DEFAULT_LEVELS = {
        'root': logging.INFO,
        'embed_repo': logging.INFO,
        'enhanced_summarizer': logging.INFO,
        'rate_limiter': logging.INFO,
        'parsers': logging.WARNING,
        'repo_state': logging.INFO,
        'change_planner': logging.INFO,
        'vector_store': logging.INFO,
        'shared.azure_services': logging.INFO,
        'shared.vector_db': logging.INFO,
        'httpx': logging.WARNING,  # Suppress verbose HTTP logs
        'asyncio': logging.WARNING,
    }
    
    # Preset configurations
    PRESETS = {
        'quiet': {
            'root': logging.WARNING,
            'embed_repo': logging.WARNING,
            'enhanced_summarizer': logging.WARNING,
            'rate_limiter': logging.WARNING,
        },
        'normal': {
            'root': logging.INFO,
            'embed_repo': logging.INFO,
            'enhanced_summarizer': logging.INFO,
            'rate_limiter': logging.INFO,
            'httpx': logging.WARNING,
        },
        'verbose': {
            'root': logging.INFO,
            'embed_repo': logging.INFO,
            'enhanced_summarizer': logging.DEBUG,
            'rate_limiter': logging.DEBUG,
            'httpx': logging.WARNING,
        },
        'debug': {
            'root': logging.DEBUG,
            'embed_repo': logging.DEBUG,
            'enhanced_summarizer': logging.DEBUG,
            'rate_limiter': logging.DEBUG,
            'parsers': logging.DEBUG,
            'repo_state': logging.DEBUG,
            'change_planner': logging.DEBUG,
            'vector_store': logging.DEBUG,
            'httpx': logging.INFO,
        },
    }
    
    @classmethod
    def configure(
        cls,
        level: str = 'normal',
        custom_levels: Optional[Dict[str, int]] = None,
        log_file: Optional[str] = None
    ):
        """
        Configure logging for code intelligence.
        
        Args:
            level: Preset level ('quiet', 'normal', 'verbose', 'debug')
            custom_levels: Custom log levels per module (overrides preset)
            log_file: Optional file path for logging
        """
        # Get preset configuration
        if level not in cls.PRESETS:
            print(f"⚠️  Unknown preset '{level}', using 'normal'")
            level = 'normal'
        
        levels = cls.PRESETS[level].copy()
        
        # Apply custom overrides
        if custom_levels:
            levels.update(custom_levels)
        
        # Configure root logger
        root_level = levels.get('root', logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Configure console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(root_level)
        console_handler.setFormatter(simple_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(root_level)
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        
        # Add file handler if requested
        if log_file:
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setLevel(logging.DEBUG)  # Always debug to file
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
            print(f"📝 Logging to file: {log_file}")
        
        # Configure specific loggers
        for module_name, module_level in levels.items():
            if module_name != 'root':
                logger = logging.getLogger(module_name)
                logger.setLevel(module_level)
        
        # Log configuration
        print(f"🔧 Logging configured: {level} mode")
        if level == 'debug':
            print("   All modules: DEBUG level")
        elif level == 'verbose':
            print("   Summarizer & Rate Limiter: DEBUG")
            print("   Other modules: INFO")
        elif level == 'normal':
            print("   Most modules: INFO level")
        elif level == 'quiet':
            print("   Most modules: WARNING level")
    
    @classmethod
    def set_level(cls, module: str, level: int):
        """
        Set log level for a specific module.
        
        Args:
            module: Module name (e.g., 'enhanced_summarizer', 'rate_limiter')
            level: Logging level (logging.DEBUG, INFO, WARNING, ERROR)
        """
        logger = logging.getLogger(module)
        logger.setLevel(level)
        print(f"🔧 Set {module} to {logging.getLevelName(level)}")


# Convenience function
def setup_logging(
    level: str = 'normal',
    log_file: Optional[str] = None,
    **custom_levels
):
    """
    Quick setup for code intelligence logging.
    
    Args:
        level: Preset level ('quiet', 'normal', 'verbose', 'debug')
        log_file: Optional file path for logging
        **custom_levels: Custom levels (e.g., rate_limiter=logging.DEBUG)
    
    Example:
        setup_logging('verbose', log_file='embedding.log')
        setup_logging('normal', rate_limiter=logging.DEBUG)
        setup_logging('debug')
    """
    custom = {k: v for k, v in custom_levels.items() if v is not None}
    CodeIntelligenceLogger.configure(level, custom, log_file)


if __name__ == "__main__":
    # Demo different presets
    print("\n" + "="*60)
    print("Logging Configuration Presets")
    print("="*60)
    
    for preset in ['quiet', 'normal', 'verbose', 'debug']:
        print(f"\n{preset.upper()} MODE:")
        levels = CodeIntelligenceLogger.PRESETS[preset]
        for module, level in sorted(levels.items()):
            print(f"  {module:30s} → {logging.getLevelName(level)}")

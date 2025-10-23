"""
Azure Configuration Validator

Separate service for validating Azure AI configuration from .env files.
Keeps validation logic separate from the main Azure AI Manager.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from shared.config import settings

logger = logging.getLogger(__name__)


class AzureConfigValidator:
    """
    Validates Azure AI configuration from .env files
    
    Provides:
    - Configuration validation
    - Missing variable detection
    - .env file management
    - Configuration status reporting
    """
    
    def __init__(self):
        self.required_vars = {
            # Azure Speech Service
            "AZURE_SPEECH_KEY": "your-azure-speech-key",
            "AZURE_SPEECH_REGION": "eastus2",
            "AZURE_SPEECH_LANG": "en-US",
            "AZURE_SPEECH_STT_ENDPOINT": "https://eastus2.stt.speech.microsoft.com",
            "AZURE_SPEECH_TTS_ENDPOINT": "https://eastus2.tts.speech.microsoft.com",
            
            # Azure Translation Service  
            "AZURE_TRANSLATION_KEY": "your-azure-translation-key",
            "AZURE_TRANSLATION_REGION": "eastus2",
            "AZURE_TRANSLATION_ENDPOINT": "https://api.cognitive.microsofttranslator.com",
            
            # Azure OpenAI Model Deployments
            "AZURE_OPENAI_ENDPOINT": "https://your-openai.cognitiveservices.azure.com/",
            "AZURE_OPENAI_API_KEY": "your-azure-openai-key",
            "AZURE_OPENAI_API_VERSION": "2024-10-21",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            
            # Azure Model Deployments (from Azure AI Foundry)
            "AZURE_GPT4O_TRANSCRIBE_DEPLOYMENT": "gpt-4o-transcribe-diarize",
            "AZURE_MODEL_ROUTER_DEPLOYMENT": "model-router", 
            "AZURE_GPT_AUDIO_MINI_DEPLOYMENT": "gpt-audio-mini",
            
            # Azure AI Services (Multi-service endpoint)
            "AZURE_AI_SERVICES_KEY": "your-azure-ai-services-key",
            "AZURE_AI_SERVICES_ENDPOINT": "https://your-ai-services.services.ai.azure.com/",
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate that all required configuration values are present in .env"""
        missing_config = []
        warnings = []
        
        # Azure Speech Service configuration
        if not settings.azure_speech_key:
            missing_config.append("AZURE_SPEECH_KEY")
        if not settings.azure_speech_region:
            missing_config.append("AZURE_SPEECH_REGION")
        
        # Azure Translation Service configuration  
        if not (settings.azure_translation_key or settings.azure_translator_key):
            missing_config.append("AZURE_TRANSLATION_KEY or AZURE_TRANSLATOR_KEY")
        if not (settings.azure_translation_region or settings.azure_translator_region):
            missing_config.append("AZURE_TRANSLATION_REGION or AZURE_TRANSLATOR_REGION")
        
        # Azure OpenAI Model Deployments
        if not settings.azure_openai_endpoint:
            missing_config.append("AZURE_OPENAI_ENDPOINT")
        if not (settings.azure_openai_api_key or settings.azure_openai_key):
            missing_config.append("AZURE_OPENAI_API_KEY")
        
        # Model deployment names (these have defaults but should be configured)
        if not settings.azure_gpt4o_transcribe_deployment:
            warnings.append("AZURE_GPT4O_TRANSCRIBE_DEPLOYMENT (using default: gpt-4o-transcribe-diarize)")
        if not settings.azure_model_router_deployment:
            warnings.append("AZURE_MODEL_ROUTER_DEPLOYMENT (using default: model-router)")
        if not settings.azure_gpt_audio_mini_deployment:
            warnings.append("AZURE_GPT_AUDIO_MINI_DEPLOYMENT (using default: gpt-audio-mini)")
        
        return {
            "missing_config": missing_config,
            "warnings": warnings,
            "is_valid": len(missing_config) == 0
        }
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get detailed configuration status from .env"""
        return {
            "azure_speech": {
                "configured": bool(settings.azure_speech_key and settings.azure_speech_region),
                "key_present": bool(settings.azure_speech_key),
                "region": settings.azure_speech_region,
                "language": settings.azure_speech_lang or "en-US",
                "stt_endpoint": settings.azure_speech_stt_endpoint,
                "tts_endpoint": settings.azure_speech_tts_endpoint
            },
            "azure_translation": {
                "configured": bool(
                    (settings.azure_translation_key or settings.azure_translator_key) and
                    (settings.azure_translation_region or settings.azure_translator_region)
                ),
                "key_present": bool(settings.azure_translation_key or settings.azure_translator_key),
                "region": settings.azure_translation_region or settings.azure_translator_region,
                "endpoint": settings.azure_translation_endpoint or settings.azure_translator_endpoint or "https://api.cognitive.microsofttranslator.com"
            },
            "azure_openai": {
                "configured": bool(
                    settings.azure_openai_endpoint and 
                    (settings.azure_openai_api_key or settings.azure_openai_key)
                ),
                "endpoint": settings.azure_openai_endpoint,
                "key_present": bool(settings.azure_openai_api_key or settings.azure_openai_key),
                "api_version": settings.azure_openai_api_version or "2024-10-21",
                "deployment_name": settings.azure_openai_deployment_name,
                "embedding_deployment": settings.azure_openai_embedding_deployment
            },
            "azure_model_deployments": {
                "gpt4o_transcribe": settings.azure_gpt4o_transcribe_deployment or "gpt-4o-transcribe-diarize",
                "model_router": settings.azure_model_router_deployment or "model-router", 
                "gpt_audio_mini": settings.azure_gpt_audio_mini_deployment or "gpt-audio-mini"
            },
            "azure_ai_services": {
                "configured": bool(settings.azure_ai_services_key and settings.azure_ai_services_endpoint),
                "key_present": bool(settings.azure_ai_services_key),
                "endpoint": settings.azure_ai_services_endpoint
            }
        }
    
    def check_missing_variables(self, update_file: bool = False) -> Dict[str, Any]:
        """
        Check for missing environment variables and optionally add them to .env
        
        Args:
            update_file: If True, adds missing variables to .env file
            
        Returns:
            Dict with missing variables and actions taken
        """
        missing_vars = []
        current_vars = {}
        
        # Check which variables are missing or empty
        for var_name, default_value in self.required_vars.items():
            current_value = os.getenv(var_name)
            current_vars[var_name] = current_value
            
            if not current_value or current_value.startswith("your-"):
                missing_vars.append(var_name)
        
        result = {
            "missing_variables": missing_vars,
            "current_variables": current_vars,
            "file_updated": False,
            "added_variables": []
        }
        
        # Add missing variables to .env file if requested
        if update_file and missing_vars:
            result.update(self._add_missing_to_env_file(missing_vars))
        
        return result
    
    def _add_missing_to_env_file(self, missing_vars: List[str]) -> Dict[str, Any]:
        """Add missing variables to .env file"""
        env_file_path = Path(".env")
        result = {"file_updated": False, "added_variables": []}
        
        try:
            # Read existing .env content
            existing_content = ""
            if env_file_path.exists():
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # Prepare new content to add
            new_content_lines = []
            if existing_content and not existing_content.endswith('\n'):
                new_content_lines.append("")  # Add newline if file doesn't end with one
            
            new_content_lines.append("# Added Azure AI configuration variables")
            
            for var_name in missing_vars:
                if var_name not in existing_content:
                    default_value = self.required_vars[var_name]
                    new_content_lines.append(f"{var_name}={default_value}")
                    result["added_variables"].append(var_name)
            
            # Write to .env file
            if result["added_variables"]:
                with open(env_file_path, 'a', encoding='utf-8') as f:
                    f.write('\n'.join(new_content_lines) + '\n')
                
                result["file_updated"] = True
                logger.info(f"✅ Added {len(result['added_variables'])} variables to .env file")
                logger.info(f"   Added: {', '.join(result['added_variables'])}")
        
        except Exception as e:
            logger.error(f"❌ Failed to update .env file: {e}")
            result["error"] = str(e)
        
        return result
    
    def log_validation_results(self):
        """Log configuration validation results"""
        validation = self.validate_configuration()
        
        if validation["missing_config"]:
            logger.warning(f"⚠️  Missing required configuration in .env: {', '.join(validation['missing_config'])}")
        if validation["warnings"]:
            logger.info(f"ℹ️  Using default values for: {', '.join(validation['warnings'])}")
        
        if validation["is_valid"]:
            logger.info("✅ All Azure AI configuration values are properly set in .env")


# Global instance
azure_config_validator = AzureConfigValidator()
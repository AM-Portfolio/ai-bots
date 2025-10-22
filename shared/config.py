from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_key_vault_url: Optional[str] = None
    
    # Primary LLM Provider (azure, together, or auto)
    # "auto" = Auto-detect based on configured credentials
    # "azure" = Use Azure OpenAI (recommended)
    llm_provider: Optional[str] = "azure"  # Default to Azure
    
    # Together AI Configuration (Fallback)
    together_api_key: Optional[str] = None
    together_model: Optional[str] = None
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_key: Optional[str] = None  # Alias for azure_openai_api_key
    azure_openai_deployment_name: Optional[str] = "gpt-4.1-mini"  # Default deployment
    azure_openai_api_version: Optional[str] = "2025-01-01-preview"  # Default API version
    azure_openai_embedding_deployment: Optional[str] = "text-embedding-ada-002"  # Default embedding
    
    # Azure Model Deployments (from Azure AI Foundry)
    azure_gpt4o_transcribe_deployment: Optional[str] = None
    azure_model_router_deployment: Optional[str] = None
    azure_gpt_audio_mini_deployment: Optional[str] = None
    
    # Azure Chat Completion Models (Common Configuration)
    # Default chat model (used by LLM factory and general chat)
    azure_chat_model: Optional[str] = "gpt-4.1-mini"  # Default chat model
    azure_chat_api_version: Optional[str] = "2025-01-01-preview"  # Chat API version
    
    # Role-Based Provider Assignment (which provider to use for specific tasks)
    # Options: 'azure', 'together', or 'auto' (uses llm_provider default)
    chat_provider: Optional[str] = "azure"           # For chat/conversation
    embedding_provider: Optional[str] = "azure"      # For embeddings
    beautify_provider: Optional[str] = "azure"       # For response beautification
    
    # Language Detection & Multilingual Support
    language_detection_enabled: Optional[bool] = None
    supported_languages: Optional[str] = None  # Comma-separated string from .env
    default_language: Optional[str] = None
    
    github_token: Optional[str] = None
    github_org: Optional[str] = None
    
    jira_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_project_key: Optional[str] = None
    jira_issue_type: Optional[str] = None
    
    confluence_url: Optional[str] = None
    confluence_email: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_space_key: Optional[str] = None
    parent_page_id: Optional[str] = None
    
    grafana_url: Optional[str] = None
    grafana_api_key: Optional[str] = None
    
    database_url: Optional[str] = None
    
    # Vector DB: Defaults to Qdrant with automatic fallback to in-memory
    vector_db_provider: Optional[str] = None
    qdrant_host: Optional[str] = None
    qdrant_port: Optional[int] = None
    vector_db_fallback_enabled: Optional[bool] = None
    
    microsoft_app_id: Optional[str] = None
    microsoft_app_password: Optional[str] = None
    
    app_host: Optional[str] = None
    app_port: Optional[int] = None
    log_level: Optional[str] = None
    environment: Optional[str] = None
    
    # Voice Assistant Settings
    voice_stt_provider: Optional[str] = None  # openai, azure, google
    voice_tts_provider: Optional[str] = None  # openai, azure, google
    voice_pause_detection_ms: Optional[int] = None
    voice_max_recording_seconds: Optional[int] = None
    voice_response_max_length: Optional[int] = None
    
    # OpenAI (for Whisper STT and TTS)
    openai_api_key: Optional[str] = None
    openai_whisper_model: Optional[str] = None
    openai_tts_model: Optional[str] = None
    openai_tts_voice: Optional[str] = None
    
    # Azure Speech Services
    azure_speech_key: Optional[str] = None
    azure_speech_region: Optional[str] = None
    azure_speech_lang: Optional[str] = None
    azure_speech_stt_endpoint: Optional[str] = None
    azure_speech_tts_endpoint: Optional[str] = None
    
    # Azure Translation Services
    azure_translation_key: Optional[str] = None
    azure_translation_region: Optional[str] = None
    azure_translation_endpoint: Optional[str] = None
    # Legacy aliases for backward compatibility
    azure_translator_key: Optional[str] = None
    azure_translator_region: Optional[str] = None
    azure_translator_endpoint: Optional[str] = None
    
    # Azure AI Services (Multi-service endpoint)
    azure_ai_services_key: Optional[str] = None
    azure_ai_services_endpoint: Optional[str] = None
    
    # Translation Settings
    enable_auto_translation: Optional[bool] = None
    translation_target_language: Optional[str] = None  # Default target for translation
    
    @property
    def port(self) -> int:
        import os
        return int(os.environ.get("PORT", self.app_port or 8000))
    
    @property
    def is_production(self) -> bool:
        return (self.environment or "development").lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return (self.environment or "development").lower() == "development"
    
    @property
    def supported_languages_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        if self.supported_languages:
            return [lang.strip() for lang in self.supported_languages.split(",")]
        return ["en", "hi"]  # Default fallback
    
    def get_with_default(self, field_name: str, default_value):
        """Get field value with fallback to default"""
        value = getattr(self, field_name, None)
        return value if value is not None else default_value


settings = Settings()

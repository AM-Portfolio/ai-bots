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
    
    # Primary LLM Provider (azure or together)
    llm_provider: str = "azure"
    
    # Together AI Configuration
    together_api_key: Optional[str] = None
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"
    
    # Role-Based Provider Assignment (which provider to use for specific tasks)
    # Options: 'azure', 'together', or 'auto' (uses llm_provider default)
    chat_provider: str = "auto"           # For chat/conversation
    embedding_provider: str = "auto"      # For embeddings
    beautify_provider: str = "auto"       # For response beautification
    
    # Language Detection & Multilingual Support
    language_detection_enabled: bool = True
    supported_languages: List[str] = ["en", "hi"]  # English, Hindi
    default_language: str = "en"
    
    github_token: Optional[str] = None
    github_org: Optional[str] = None
    
    jira_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_project_key: Optional[str] = None
    jira_issue_type: str = "Task"
    
    confluence_url: Optional[str] = None
    confluence_email: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_space_key: Optional[str] = None
    parent_page_id: Optional[str] = None
    
    grafana_url: Optional[str] = None
    grafana_api_key: Optional[str] = None
    
    database_url: str = "sqlite:///./ai_dev_agent.db"
    
    # Vector DB: Defaults to Qdrant with automatic fallback to in-memory
    vector_db_provider: str = "qdrant"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    vector_db_fallback_enabled: bool = True
    
    microsoft_app_id: Optional[str] = None
    microsoft_app_password: Optional[str] = None
    
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    environment: str = "development"
    
    # Voice Assistant Settings
    voice_stt_provider: str = "openai"  # openai, azure, google
    voice_tts_provider: str = "openai"  # openai, azure, google
    voice_pause_detection_ms: int = 1500
    voice_max_recording_seconds: int = 60
    voice_response_max_length: int = 500
    
    # OpenAI (for Whisper STT and TTS)
    openai_api_key: Optional[str] = None
    openai_whisper_model: str = "whisper-1"
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "nova"
    
    # Azure Speech Services
    azure_speech_key: Optional[str] = None
    azure_speech_region: str = "eastus"
    azure_speech_lang: str = "en-US"
    
    @property
    def port(self) -> int:
        import os
        return int(os.environ.get("PORT", self.app_port))
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


settings = Settings()

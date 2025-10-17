from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


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
    
    llm_provider: str = "together"
    
    together_api_key: Optional[str] = None
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-15-preview"
    
    github_token: Optional[str] = None
    github_org: Optional[str] = None
    
    jira_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    
    confluence_url: Optional[str] = None
    confluence_email: Optional[str] = None
    confluence_api_token: Optional[str] = None
    
    grafana_url: Optional[str] = None
    grafana_api_key: Optional[str] = None
    
    database_url: str = "sqlite:///./ai_dev_agent.db"
    
    microsoft_app_id: Optional[str] = None
    microsoft_app_password: Optional[str] = None
    
    app_host: str = "0.0.0.0"
    app_port: int = 5000
    log_level: str = "INFO"
    environment: str = "development"
    
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

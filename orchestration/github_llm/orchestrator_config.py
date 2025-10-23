"""
GitHub-LLM Orchestrator Configuration

Centralized configuration for the GitHub-LLM query orchestration system.
"""

from dataclasses import dataclass
from typing import Optional
from shared.config import settings


@dataclass
class GitHubLLMConfig:
    """Configuration for GitHub-LLM Orchestrator"""
    
    # API Endpoints
    code_intelligence_api_url: str
    
    # Vector Database
    collection_name: str
    
    # LLM Settings
    llm_provider: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    
    # Query Settings
    default_max_results: int
    min_confidence_threshold: float
    
    # HTTP Settings
    http_timeout: float
    
    # Feature Flags
    enable_beautification: bool
    enable_github_direct: bool
    enable_vector_search: bool
    
    @classmethod
    def from_settings(cls) -> "GitHubLLMConfig":
        """Create config from global settings"""
        # Determine API base URL
        api_host = settings.app_host or "localhost"
        api_port = settings.app_port or 8000
        code_intel_api_url = f"http://{api_host}:{api_port}/api/code-intelligence"
        
        # Get LLM provider and model
        llm_provider = settings.llm_provider or settings.chat_provider or "azure"
        
        # Get model/deployment name based on provider
        if llm_provider == "azure":
            llm_model = (
                settings.azure_openai_deployment_name or
                settings.azure_chat_model or
                settings.azure_gpt4o_transcribe_deployment or
                "gpt-4"
            )
        elif llm_provider == "together":
            llm_model = settings.together_model or "meta-llama/Llama-3-70b-chat-hf"
        else:
            llm_model = "gpt-4"
        
        return cls(
            # API Endpoints
            code_intelligence_api_url=code_intel_api_url,
            
            # Vector Database
            collection_name=settings.vector_db_collection_name or "code_intelligence",
            
            # LLM Settings
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_temperature=0.3,  # Conservative for code queries
            llm_max_tokens=2000,
            
            # Query Settings
            default_max_results=5,
            min_confidence_threshold=0.3,
            
            # HTTP Settings
            http_timeout=30.0,
            
            # Feature Flags
            enable_beautification=True,
            enable_github_direct=False,  # Not implemented yet
            enable_vector_search=True
        )

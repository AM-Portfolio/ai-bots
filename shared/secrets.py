from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class SecretsManager:
    def __init__(self):
        self.client: Optional[SecretClient] = None
        self._initialize_client()
    
    def _initialize_client(self):
        if not settings.azure_key_vault_url:
            logger.warning("Azure Key Vault URL not configured. Secrets will not be available.")
            return
        
        try:
            if all([settings.azure_tenant_id, settings.azure_client_id, settings.azure_client_secret]):
                credential = ClientSecretCredential(
                    tenant_id=settings.azure_tenant_id,
                    client_id=settings.azure_client_id,
                    client_secret=settings.azure_client_secret
                )
            else:
                credential = DefaultAzureCredential()
            
            self.client = SecretClient(
                vault_url=settings.azure_key_vault_url,
                credential=credential
            )
            logger.info("Azure Key Vault client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {e}")
            self.client = None
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        if not self.client:
            logger.warning(f"Key Vault client not initialized. Cannot retrieve secret: {secret_name}")
            return None
        
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            return None
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        if not self.client:
            logger.warning(f"Key Vault client not initialized. Cannot set secret: {secret_name}")
            return False
        
        try:
            self.client.set_secret(secret_name, secret_value)
            logger.info(f"Secret {secret_name} set successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {secret_name}: {e}")
            return False


secrets_manager = SecretsManager()

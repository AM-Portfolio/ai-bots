"""Base service interface for all integrations"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

from shared.logger import get_logger

logger = get_logger(__name__)


class ServiceStatus(str, Enum):
    """Service connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TESTING = "testing"


class ServiceConfig(BaseModel):
    """Base configuration for services"""
    service_name: str
    service_type: str
    enabled: bool = True
    config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class BaseService(ABC):
    """Base class for all service integrations"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.status = ServiceStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.last_connected: Optional[datetime] = None
        self._client: Optional[Any] = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the service"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the service"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test if the service is accessible"""
        pass
    
    @abstractmethod
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a service-specific action"""
        pass
    
    async def get_capabilities(self) -> List[str]:
        """Get list of service capabilities"""
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": self.config.service_name,
            "status": self.status.value,
            "last_error": self.last_error,
            "last_connected": self.last_connected.isoformat() if self.last_connected else None
        }
    
    def _set_connected(self):
        """Mark service as connected"""
        self.status = ServiceStatus.CONNECTED
        self.last_connected = datetime.now()
        self.last_error = None
    
    def _set_error(self, error: str):
        """Mark service as error"""
        self.status = ServiceStatus.ERROR
        self.last_error = error
        logger.error(f"{self.config.service_name} error: {error}")

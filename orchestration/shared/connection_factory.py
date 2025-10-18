"""
Connection Factory Module
Creates service connections using IntegrationsHub configured credentials
"""
import logging
from typing import Optional, Dict, Any
from shared.services.manager import ServiceManager

logger = logging.getLogger(__name__)


class ConnectionFactory:
    """Factory for creating service connections from IntegrationsHub configurations"""
    
    def __init__(self):
        self.service_manager = ServiceManager()
        self._initialized = False
        logger.info("🏭 Connection factory initialized")
    
    async def initialize_from_integrations(self) -> None:
        """Initialize service connections from IntegrationsHub configurations"""
        if self._initialized:
            return
        
        try:
            import sys
            from pathlib import Path
            # Add project root to path
            project_root = Path(__file__).parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from data.repositories.integration_repository import IntegrationRepository
            from data.database import SessionLocal
            
            logger.info("📡 Loading integrations from database...")
            
            # Create a synchronous database session
            db = SessionLocal()
            try:
                integration_repo = IntegrationRepository(db)
                # Convert async method to sync since we're using sync session
                integrations = db.query(integration_repo.model).all()
                
                logger.info(f"📋 Found {len(integrations)} configured integrations")
                
                for integration in integrations:
                    if not integration.enabled or integration.status != 'connected':
                        logger.debug(f"⏭️  Skipping {integration.service_name} (not enabled/connected)")
                        continue
                    
                    logger.info(f"🔌 Connecting {integration.service_name}...")
                    
                    try:
                        await self._register_service(integration)
                        logger.info(f"✅ {integration.service_name} connected successfully")
                    except Exception as e:
                        logger.error(f"❌ Failed to connect {integration.service_name}: {str(e)}")
            finally:
                db.close()
            
            self._initialized = True
            logger.info("✅ Connection factory initialized with all integrations")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection factory: {str(e)}")
            # Don't raise - allow system to continue without integrations
            self._initialized = True  # Mark as initialized even if failed to prevent retry loops
    
    async def _register_service(self, integration) -> None:
        """Register a service with the service manager based on integration config"""
        service_name = integration.service_name.lower()
        config = integration.configuration or {}
        
        if service_name == 'github':
            await self._register_github(config)
        elif service_name == 'confluence':
            await self._register_confluence(config)
        elif service_name == 'jira':
            await self._register_jira(config)
        elif service_name == 'grafana':
            await self._register_grafana(config)
        elif service_name == 'postgresql':
            await self._register_postgresql(config)
        elif service_name == 'mongodb':
            await self._register_mongodb(config)
        else:
            logger.warning(f"⚠️  Unknown service type: {service_name}")
    
    async def _register_github(self, config: Dict[str, Any]) -> None:
        """Register GitHub service"""
        token = config.get('token') or config.get('api_key')
        if not token:
            raise ValueError("GitHub token not found in configuration")
        
        await self.service_manager.register_service(
            service_name='github',
            service_type='github',
            config={'token': token}
        )
    
    async def _register_confluence(self, config: Dict[str, Any]) -> None:
        """Register Confluence service"""
        url = config.get('url')
        username = config.get('username')
        api_token = config.get('api_token')
        
        if not all([url, username, api_token]):
            raise ValueError("Confluence configuration incomplete")
        
        await self.service_manager.register_service(
            service_name='confluence',
            service_type='confluence',
            config={
                'url': url,
                'username': username,
                'api_token': api_token
            }
        )
    
    async def _register_jira(self, config: Dict[str, Any]) -> None:
        """Register Jira service"""
        url = config.get('url')
        username = config.get('username')
        api_token = config.get('api_token')
        
        if not all([url, username, api_token]):
            raise ValueError("Jira configuration incomplete")
        
        await self.service_manager.register_service(
            service_name='jira',
            service_type='jira',
            config={
                'url': url,
                'username': username,
                'api_token': api_token
            }
        )
    
    async def _register_grafana(self, config: Dict[str, Any]) -> None:
        """Register Grafana service"""
        url = config.get('url')
        api_key = config.get('api_key')
        
        if not all([url, api_key]):
            raise ValueError("Grafana configuration incomplete")
        
        await self.service_manager.register_service(
            service_name='grafana',
            service_type='grafana',
            config={
                'url': url,
                'api_key': api_key
            }
        )
    
    async def _register_postgresql(self, config: Dict[str, Any]) -> None:
        """Register PostgreSQL service"""
        connection_string = config.get('connection_string')
        if not connection_string:
            raise ValueError("PostgreSQL connection string not found")
        
        await self.service_manager.register_service(
            service_name='postgresql',
            service_type='postgresql',
            config={'connection_string': connection_string}
        )
    
    async def _register_mongodb(self, config: Dict[str, Any]) -> None:
        """Register MongoDB service"""
        connection_string = config.get('connection_string')
        if not connection_string:
            raise ValueError("MongoDB connection string not found")
        
        await self.service_manager.register_service(
            service_name='mongodb',
            service_type='mongodb',
            config={'connection_string': connection_string}
        )
    
    def get_service_manager(self) -> ServiceManager:
        """Get the initialized service manager"""
        return self.service_manager
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available"""
        return self.service_manager.get_service(service_name) is not None


# Global factory instance
_factory: Optional[ConnectionFactory] = None


async def get_connection_factory() -> ConnectionFactory:
    """Get or create the global connection factory instance"""
    global _factory
    
    if _factory is None:
        _factory = ConnectionFactory()
        await _factory.initialize_from_integrations()
    
    return _factory


async def get_service_manager() -> ServiceManager:
    """Get the service manager from the connection factory"""
    factory = await get_connection_factory()
    return factory.get_service_manager()

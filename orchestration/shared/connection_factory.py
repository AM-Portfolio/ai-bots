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
            # First try to initialize from database
            await self._initialize_from_database()
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            logger.info("Falling back to environment variable initialization...")
            
        # Always try environment variable initialization as fallback
        await self._initialize_from_env()
        
        self._initialized = True
        logger.info("✅ Connection factory initialization complete")
    
    async def _initialize_from_database(self) -> None:
        """Initialize from database integrations"""
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
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            raise
    
    async def _initialize_from_env(self) -> None:
        """Initialize services from environment variables as fallback"""
        from shared.config import settings
        
        logger.info("🌱 Initializing services from environment variables...")
        
        # GitHub service
        if settings.github_token:
            try:
                await self._register_github_from_env(settings.github_token, settings.github_org)
                logger.info("✅ GitHub service initialized from environment")
            except Exception as e:
                logger.error(f"❌ Failed to initialize GitHub from env: {e}")
        else:
            logger.warning("⚠️  GitHub token not found in environment variables")
        
        # Jira service
        if settings.jira_url and settings.jira_email and settings.jira_api_token:
            try:
                await self._register_jira_from_env(
                    settings.jira_url, 
                    settings.jira_email, 
                    settings.jira_api_token
                )
                logger.info("✅ Jira service initialized from environment")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Jira from env: {e}")
        
        # Confluence service
        if settings.confluence_url and settings.confluence_email and settings.confluence_api_token:
            try:
                await self._register_confluence_from_env(
                    settings.confluence_url,
                    settings.confluence_email,
                    settings.confluence_api_token
                )
                logger.info("✅ Confluence service initialized from environment")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Confluence from env: {e}")
        
        # Grafana service
        if settings.grafana_url and settings.grafana_api_key:
            try:
                await self._register_grafana_from_env(
                    settings.grafana_url,
                    settings.grafana_api_key
                )
                logger.info("✅ Grafana service initialized from environment")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Grafana from env: {e}")
    
    async def _register_github_from_env(self, token: str, org: Optional[str] = None) -> None:
        """Register GitHub service from environment variables"""
        if not self.service_manager.get_service('github'):
            config = {'token': token}
            if org:
                config['org'] = org
            await self._register_github(config)
    
    async def _register_jira_from_env(self, url: str, email: str, api_token: str) -> None:
        """Register Jira service from environment variables"""
        if not self.service_manager.get_service('jira'):
            await self._register_jira({
                'url': url,
                'username': email,
                'api_token': api_token
            })
    
    async def _register_confluence_from_env(self, url: str, email: str, api_token: str) -> None:
        """Register Confluence service from environment variables"""
        if not self.service_manager.get_service('confluence'):
            await self._register_confluence({
                'url': url,
                'username': email,
                'api_token': api_token
            })
    
    async def _register_grafana_from_env(self, url: str, api_key: str) -> None:
        """Register Grafana service from environment variables"""
        if not self.service_manager.get_service('grafana'):
            await self._register_grafana({
                'url': url,
                'api_key': api_key
            })
    
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
        from shared.services.integrations.github_service import GitHubService
        from shared.services.base import ServiceConfig
        
        token = config.get('token') or config.get('api_key')
        if not token:
            raise ValueError("GitHub token not found in configuration")
        
        service_config = ServiceConfig(
            service_name='github',
            service_type='github',
            config={'token': token}
        )
        
        github_service = GitHubService(service_config)
        await self.service_manager.register_service(github_service)
        await self.service_manager.connect_service('github')
    
    async def _register_confluence(self, config: Dict[str, Any]) -> None:
        """Register Confluence service"""
        from shared.services.integrations.confluence_service import ConfluenceService
        from shared.services.base import ServiceConfig
        
        url = config.get('url')
        username = config.get('username')
        api_token = config.get('api_token')
        
        if not all([url, username, api_token]):
            raise ValueError("Confluence configuration incomplete")
        
        service_config = ServiceConfig(
            service_name='confluence',
            service_type='confluence',
            config={
                'url': url,
                'username': username,
                'api_token': api_token
            }
        )
        
        confluence_service = ConfluenceService(service_config)
        await self.service_manager.register_service(confluence_service)
        await self.service_manager.connect_service('confluence')
    
    async def _register_jira(self, config: Dict[str, Any]) -> None:
        """Register Jira service"""
        # For now, just log that Jira would be registered
        # We don't have a JiraService implementation yet
        url = config.get('url')
        username = config.get('username')
        api_token = config.get('api_token')
        
        if not all([url, username, api_token]):
            raise ValueError("Jira configuration incomplete")
            
        logger.info(f"Jira service registration not implemented yet: {url}")
    
    async def _register_grafana(self, config: Dict[str, Any]) -> None:
        """Register Grafana service"""
        # For now, just log that Grafana would be registered
        # We don't have a GrafanaService implementation yet
        url = config.get('url')
        api_key = config.get('api_key')
        
        if not all([url, api_key]):
            raise ValueError("Grafana configuration incomplete")
            
        logger.info(f"Grafana service registration not implemented yet: {url}")
    async def _register_postgresql(self, config: Dict[str, Any]) -> None:
        """Register PostgreSQL service"""
        # For now, just log that PostgreSQL would be registered
        connection_string = config.get('connection_string')
        if not connection_string:
            raise ValueError("PostgreSQL connection string not found")
        
        logger.info(f"PostgreSQL service registration not implemented yet")
    
    async def _register_mongodb(self, config: Dict[str, Any]) -> None:
        """Register MongoDB service"""
        from shared.services.integrations.mongodb_service import MongoDBService
        from shared.services.base import ServiceConfig
        
        connection_string = config.get('connection_string')
        if not connection_string:
            raise ValueError("MongoDB connection string not found")
        
        service_config = ServiceConfig(
            service_name='mongodb',
            service_type='mongodb',
            config={'connection_string': connection_string}
        )
        
        mongodb_service = MongoDBService(service_config)
        await self.service_manager.register_service(mongodb_service)
        await self.service_manager.connect_service('mongodb')
    
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

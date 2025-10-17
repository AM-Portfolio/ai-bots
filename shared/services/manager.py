"""Service manager for connection pooling and lifecycle management"""

from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta

from .base import BaseService, ServiceConfig, ServiceStatus
from .llm_wrapper import ServiceLLMWrapper, LLMServiceContext
from shared.logger import get_logger

logger = get_logger(__name__)


class ServiceManager:
    """Manages service lifecycle, connections, and LLM-powered interactions"""
    
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._llm_wrapper = ServiceLLMWrapper()
        self._connection_pool: Dict[str, datetime] = {}
    
    async def register_service(self, service: BaseService) -> bool:
        """Register a new service"""
        try:
            service_name = service.config.service_name
            
            if service_name in self._services:
                logger.warning(f"Service {service_name} already registered, replacing")
            
            self._services[service_name] = service
            logger.info(f"Registered service: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            return False
    
    async def connect_service(self, service_name: str) -> bool:
        """Connect to a service"""
        service = self._services.get(service_name)
        if not service:
            logger.error(f"Service {service_name} not found")
            return False
        
        try:
            result = await service.connect()
            if result:
                self._connection_pool[service_name] = datetime.now()
            return result
        except Exception as e:
            logger.error(f"Failed to connect to {service_name}: {e}")
            service._set_error(str(e))
            return False
    
    async def disconnect_service(self, service_name: str) -> bool:
        """Disconnect from a service"""
        service = self._services.get(service_name)
        if not service:
            return False
        
        try:
            result = await service.disconnect()
            if result and service_name in self._connection_pool:
                del self._connection_pool[service_name]
            return result
        except Exception as e:
            logger.error(f"Failed to disconnect from {service_name}: {e}")
            return False
    
    async def execute_with_llm(
        self,
        service_name: str,
        action: str,
        use_llm_enhancement: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute service action with optional LLM enhancement"""
        service = self._services.get(service_name)
        if not service:
            return {"success": False, "error": f"Service {service_name} not found"}
        
        try:
            # Ensure service is connected
            if service.status != ServiceStatus.CONNECTED:
                connected = await self.connect_service(service_name)
                if not connected:
                    return {"success": False, "error": "Failed to connect to service"}
            
            # LLM enhancement (optional)
            enhanced_params = kwargs
            if use_llm_enhancement:
                capabilities = await service.get_capabilities()
                context = LLMServiceContext(
                    service_name=service_name,
                    action=action,
                    input_data=kwargs,
                    service_capabilities=capabilities
                )
                enhancement = await self._llm_wrapper.enhance_query(context)
                if enhancement.get("enhanced"):
                    logger.info(f"LLM enhanced query for {service_name}.{action}")
                    enhanced_params = enhancement.get("suggestion", kwargs)
            
            # Execute action
            result = await service.execute(action, **enhanced_params)
            
            # LLM interpretation (optional)
            if use_llm_enhancement and result.get("success"):
                context = LLMServiceContext(
                    service_name=service_name,
                    action=action,
                    input_data=enhanced_params,
                    service_capabilities=await service.get_capabilities()
                )
                interpretation = await self._llm_wrapper.interpret_response(context, result)
                result["llm_insights"] = interpretation.get("interpretation")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Service execution failed for {service_name}.{action}: {error_msg}")
            
            # LLM error analysis
            if use_llm_enhancement:
                error_analysis = await self._llm_wrapper.handle_error(
                    service_name, error_msg, {"action": action, "params": kwargs}
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "llm_analysis": error_analysis.get("analysis")
                }
            
            return {"success": False, "error": error_msg}
    
    async def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered services"""
        return {
            name: service.get_status()
            for name, service in self._services.items()
        }
    
    async def cleanup_stale_connections(self, max_idle_minutes: int = 30):
        """Cleanup connections idle for too long"""
        cutoff = datetime.now() - timedelta(minutes=max_idle_minutes)
        stale_services = [
            name for name, last_used in self._connection_pool.items()
            if last_used < cutoff
        ]
        
        for service_name in stale_services:
            logger.info(f"Cleaning up stale connection: {service_name}")
            await self.disconnect_service(service_name)
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """Get a registered service"""
        return self._services.get(service_name)
    
    def list_services(self) -> List[str]:
        """List all registered service names"""
        return list(self._services.keys())


# Global service manager instance
service_manager = ServiceManager()

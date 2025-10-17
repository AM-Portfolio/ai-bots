"""API endpoints for service management"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from shared.services.manager import service_manager
from shared.services.base import ServiceConfig
from shared.services.integrations import GitHubService, ConfluenceService, MongoDBService
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/services", tags=["services"])


class ServiceConnectionRequest(BaseModel):
    """Request to connect to a service"""
    service_name: str
    service_type: str
    config: Dict[str, Any]


class ServiceActionRequest(BaseModel):
    """Request to execute service action"""
    service_name: str
    action: str
    params: Dict[str, Any] = {}
    use_llm: bool = True


@router.post("/connect")
async def connect_service(request: ServiceConnectionRequest):
    """Connect to a service"""
    try:
        # Create service instance
        service_config = ServiceConfig(
            service_name=request.service_name,
            service_type=request.service_type,
            config=request.config
        )
        
        # Map service type to service class
        service_classes = {
            "github": GitHubService,
            "confluence": ConfluenceService,
            "mongodb": MongoDBService
        }
        
        service_class = service_classes.get(request.service_type.lower())
        if not service_class:
            return {
                "success": False,
                "error": f"Unknown service type: {request.service_type}"
            }
        
        # Create and register service
        service = service_class(service_config)
        await service_manager.register_service(service)
        
        # Connect
        connected = await service_manager.connect_service(request.service_name)
        
        if connected:
            return {
                "success": True,
                "message": f"Connected to {request.service_name}",
                "status": service.get_status()
            }
        else:
            return {
                "success": False,
                "error": f"Failed to connect to {request.service_name}",
                "status": service.get_status()
            }
            
    except Exception as e:
        logger.error(f"Service connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect/{service_name}")
async def disconnect_service(service_name: str):
    """Disconnect from a service"""
    try:
        result = await service_manager.disconnect_service(service_name)
        return {"success": result, "service": service_name}
    except Exception as e:
        logger.error(f"Service disconnection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_action(request: ServiceActionRequest):
    """Execute a service action with optional LLM enhancement"""
    try:
        result = await service_manager.execute_with_llm(
            service_name=request.service_name,
            action=request.action,
            use_llm_enhancement=request.use_llm,
            **request.params
        )
        return result
    except Exception as e:
        logger.error(f"Service execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_all_statuses():
    """Get status of all services"""
    try:
        statuses = await service_manager.get_all_statuses()
        return {"success": True, "services": statuses}
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{service_name}")
async def get_service_status(service_name: str):
    """Get status of a specific service"""
    try:
        service = service_manager.get_service(service_name)
        if not service:
            return {"success": False, "error": "Service not found"}
        
        return {
            "success": True,
            "status": service.get_status(),
            "capabilities": await service.get_capabilities()
        }
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_services():
    """List all registered services"""
    try:
        services = service_manager.list_services()
        return {"success": True, "services": services}
    except Exception as e:
        logger.error(f"Service listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/{service_name}")
async def test_service(service_name: str):
    """Test a service connection"""
    try:
        service = service_manager.get_service(service_name)
        if not service:
            return {"success": False, "error": "Service not found"}
        
        result = await service.test_connection()
        return result
    except Exception as e:
        logger.error(f"Service test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

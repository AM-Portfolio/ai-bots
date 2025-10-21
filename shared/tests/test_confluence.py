"""Test Confluence connection and operations"""
import asyncio
import logging
from typing import Dict, Any
from shared.config import settings
from shared.clients.confluence_replit_client import confluence_replit_client

logger = logging.getLogger(__name__)


async def test_confluence_connection() -> Dict[str, Any]:
    """Test Confluence connection"""
    result = {
        "service": "Confluence API",
        "configured": bool(settings.confluence_url and settings.confluence_email and settings.confluence_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        missing = []
        if not settings.confluence_url:
            missing.append("URL")
        if not settings.confluence_email:
            missing.append("email")
        if not settings.confluence_api_token:
            missing.append("API token")
        result["error"] = f"Confluence credentials not configured: missing {', '.join(missing)}"
        return result
    
    try:
        # Test connection using our client
        connection_test = await confluence_replit_client.test_connection()
        
        if connection_test:
            result["connection"] = True
            result["details"] = {
                "url": settings.confluence_url,
                "email": settings.confluence_email,
                "space_key": settings.confluence_space_key,
                "parent_page_id": settings.parent_page_id
            }
        else:
            result["error"] = "Connection test failed"
        
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_confluence_spaces() -> Dict[str, Any]:
    """Test Confluence spaces access"""
    result = {
        "service": "Confluence Spaces",
        "configured": bool(settings.confluence_url and settings.confluence_email and settings.confluence_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Confluence credentials not configured"
        return result
    
    try:
        # Test getting spaces
        spaces = await confluence_replit_client.get_spaces()
        
        if spaces:
            result["connection"] = True
            result["details"] = {
                "total_spaces": len(spaces),
                "default_space_key": settings.confluence_space_key,
                "available_spaces": [{"key": s.get("key"), "name": s.get("name")} for s in spaces[:5]]  # First 5
            }
        else:
            result["error"] = "No spaces found or access denied"
        
    except Exception as e:
        result["error"] = f"Spaces access failed: {e}"
    
    return result


async def test_confluence_space_access() -> Dict[str, Any]:
    """Test access to configured space"""
    result = {
        "service": "Confluence Space Access",
        "configured": bool(settings.confluence_space_key and settings.confluence_url and settings.confluence_email and settings.confluence_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Confluence space key or credentials not configured"
        return result
    
    try:
        # Test getting space info
        space_info = await confluence_replit_client.get_space_info(settings.confluence_space_key)
        
        if space_info:
            # Try to get pages in the space
            pages = await confluence_replit_client.get_pages_in_space(settings.confluence_space_key, limit=5)
            
            result["connection"] = True
            result["details"] = {
                "space_key": settings.confluence_space_key,
                "space_name": space_info.get("name"),
                "space_type": space_info.get("type"),
                "pages_count": len(pages) if pages else 0,
                "sample_pages": [{"id": p.get("id"), "title": p.get("title")} for p in (pages or [])[:3]]
            }
        else:
            result["error"] = "Space not found or access denied"
        
    except Exception as e:
        result["error"] = f"Space access failed: {e}"
    
    return result


async def test_confluence_create_test_page() -> Dict[str, Any]:
    """Test creating a test page (will be deleted)"""
    result = {
        "service": "Confluence Page Creation",
        "configured": bool(settings.confluence_space_key and settings.confluence_url and settings.confluence_email and settings.confluence_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Confluence space key or credentials not configured"
        return result
    
    try:
        # Create a test page
        test_title = f"Connection Test - {asyncio.get_event_loop().time()}"
        test_content = "<p>This is a test page created by the AI bot connection test. It will be deleted automatically.</p>"
        
        page = await confluence_replit_client.create_page(
            space_key=settings.confluence_space_key,
            title=test_title,
            content=test_content,
            parent_id=settings.parent_page_id
        )
        
        if page:
            # Try to delete the test page
            page_id = page.get("id")
            if page_id:
                try:
                    await confluence_replit_client.delete_page(page_id)
                    deletion_status = "deleted"
                except:
                    deletion_status = "failed to delete"
            else:
                deletion_status = "no page ID"
            
            result["connection"] = True
            result["details"] = {
                "test_page_created": True,
                "page_id": page_id,
                "page_url": page.get("url"),
                "deletion_status": deletion_status
            }
        else:
            result["error"] = "Failed to create test page"
        
    except Exception as e:
        result["error"] = f"Page creation test failed: {e}"
    
    return result


async def test_all_confluence_services() -> Dict[str, Any]:
    """Test all Confluence services"""
    logger.info("Testing Confluence services...")
    
    results = {}
    
    # Test basic connection
    results["connection"] = await test_confluence_connection()
    
    # Test other services only if connection works
    if results["connection"]["connection"]:
        results["spaces"] = await test_confluence_spaces()
        results["space_access"] = await test_confluence_space_access()
        results["page_creation"] = await test_confluence_create_test_page()
    else:
        results["spaces"] = {
            "service": "Confluence Spaces",
            "configured": False,
            "connection": False,
            "error": "Skipped due to connection failure",
            "details": {}
        }
        results["space_access"] = {
            "service": "Confluence Space Access",
            "configured": False,
            "connection": False,
            "error": "Skipped due to connection failure",
            "details": {}
        }
        results["page_creation"] = {
            "service": "Confluence Page Creation",
            "configured": False,
            "connection": False,
            "error": "Skipped due to connection failure",
            "details": {}
        }
    
    # Summary
    total_services = len(results)
    connected_services = sum(1 for r in results.values() if r["connection"])
    configured_services = sum(1 for r in results.values() if r["configured"])
    
    results["summary"] = {
        "total_services": total_services,
        "configured_services": configured_services,
        "connected_services": connected_services,
        "success_rate": f"{connected_services}/{configured_services}" if configured_services > 0 else "0/0"
    }
    
    return results


if __name__ == "__main__":
    async def main():
        print("Testing Confluence connections...")
        results = await test_all_confluence_services()
        
        print(f"\n=== Confluence Test Results ===")
        for service_key, result in results.items():
            if service_key == "summary":
                continue
            print(f"\n{result['service']}:")
            print(f"  Configured: {result['configured']}")
            print(f"  Connected: {result['connection']}")
            if result['error']:
                print(f"  Error: {result['error']}")
            if result['details']:
                print(f"  Details: {result['details']}")
        
        print(f"\n=== Summary ===")
        summary = results["summary"]
        print(f"Services configured: {summary['configured_services']}/{summary['total_services']}")
        print(f"Services connected: {summary['connected_services']}/{summary['configured_services']}")
        print(f"Success rate: {summary['success_rate']}")
    
    asyncio.run(main())
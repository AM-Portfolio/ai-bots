"""Test Jira connection and operations"""
import asyncio
import logging
from typing import Dict, Any
from shared.config import settings
from shared.clients.jira_client import get_jira_client

logger = logging.getLogger(__name__)


async def test_jira_connection() -> Dict[str, Any]:
    """Test Jira connection"""
    result = {
        "service": "Jira API",
        "configured": bool(settings.jira_url and settings.jira_email and settings.jira_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        missing = []
        if not settings.jira_url:
            missing.append("URL")
        if not settings.jira_email:
            missing.append("email")
        if not settings.jira_api_token:
            missing.append("API token")
        result["error"] = f"Jira credentials not configured: missing {', '.join(missing)}"
        return result
    
    try:
        # Test connection using our client
        jira_client = get_jira_client()
        if jira_client.client:
            # Try to get current user info
            user = jira_client.client.current_user()
            
            result["connection"] = True
            result["details"] = {
                "url": settings.jira_url,
                "email": settings.jira_email,
                "user": user,
                "project_key": settings.jira_project_key,
                "issue_type": settings.jira_issue_type
            }
        else:
            result["error"] = "Jira client not initialized"
        
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_jira_projects() -> Dict[str, Any]:
    """Test Jira projects access"""
    result = {
        "service": "Jira Projects",
        "configured": bool(settings.jira_url and settings.jira_email and settings.jira_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Jira credentials not configured"
        return result
    
    try:
        jira_client = get_jira_client()
        if not jira_client.client:
            result["error"] = "Jira client not initialized"
            return result
        
        # Get all projects
        projects = jira_client.client.projects()
        
        result["connection"] = True
        result["details"] = {
            "total_projects": len(projects),
            "default_project_key": settings.jira_project_key,
            "available_projects": [{"key": p.key, "name": p.name} for p in projects[:5]]  # First 5
        }
        
    except Exception as e:
        result["error"] = f"Projects access failed: {e}"
    
    return result


async def test_jira_project_access() -> Dict[str, Any]:
    """Test access to configured project"""
    result = {
        "service": "Jira Project Access",
        "configured": bool(settings.jira_project_key and settings.jira_url and settings.jira_email and settings.jira_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Jira project key or credentials not configured"
        return result
    
    try:
        jira_client = get_jira_client()
        if not jira_client.client:
            result["error"] = "Jira client not initialized"
            return result
        
        # Get project info
        project = jira_client.client.project(settings.jira_project_key)
        
        # Get recent issues in the project
        issues = jira_client.client.search_issues(
            f'project = {settings.jira_project_key}',
            maxResults=5
        )
        
        # Get issue types for the project
        issue_types = jira_client.client.issue_types()
        
        result["connection"] = True
        result["details"] = {
            "project_key": settings.jira_project_key,
            "project_name": project.name,
            "project_lead": project.lead.displayName if hasattr(project, 'lead') and project.lead else "N/A",
            "recent_issues_count": len(issues),
            "sample_issues": [{"key": i.key, "summary": i.fields.summary} for i in issues[:3]],
            "available_issue_types": [it.name for it in issue_types[:5]]
        }
        
    except Exception as e:
        result["error"] = f"Project access failed: {e}"
    
    return result


async def test_jira_create_test_issue() -> Dict[str, Any]:
    """Test creating a test issue (will be deleted)"""
    result = {
        "service": "Jira Issue Creation",
        "configured": bool(settings.jira_project_key and settings.jira_url and settings.jira_email and settings.jira_api_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Jira project key or credentials not configured"
        return result
    
    try:
        jira_client = get_jira_client()
        if not jira_client.client:
            result["error"] = "Jira client not initialized"
            return result
        
        # Create a test issue
        issue_dict = {
            'project': {'key': settings.jira_project_key},
            'summary': f'Connection Test - {asyncio.get_event_loop().time()}',
            'description': 'This is a test issue created by the AI bot connection test. It can be deleted.',
            'issuetype': {'name': settings.jira_issue_type}
        }
        
        new_issue = jira_client.client.create_issue(fields=issue_dict)
        
        if new_issue:
            # Try to delete the test issue
            try:
                new_issue.delete()
                deletion_status = "deleted"
            except:
                deletion_status = "failed to delete (may not have permission)"
            
            result["connection"] = True
            result["details"] = {
                "test_issue_created": True,
                "issue_key": new_issue.key,
                "issue_url": f"{settings.jira_url}/browse/{new_issue.key}",
                "deletion_status": deletion_status
            }
        else:
            result["error"] = "Failed to create test issue"
        
    except Exception as e:
        result["error"] = f"Issue creation test failed: {e}"
    
    return result


async def test_all_jira_services() -> Dict[str, Any]:
    """Test all Jira services"""
    logger.info("Testing Jira services...")
    
    results = {}
    
    # Test basic connection
    results["connection"] = await test_jira_connection()
    
    # Test other services only if connection works
    if results["connection"]["connection"]:
        results["projects"] = await test_jira_projects()
        results["project_access"] = await test_jira_project_access()
        results["issue_creation"] = await test_jira_create_test_issue()
    else:
        results["projects"] = {
            "service": "Jira Projects",
            "configured": False,
            "connection": False,
            "error": "Skipped due to connection failure",
            "details": {}
        }
        results["project_access"] = {
            "service": "Jira Project Access",
            "configured": False,
            "connection": False,
            "error": "Skipped due to connection failure",
            "details": {}
        }
        results["issue_creation"] = {
            "service": "Jira Issue Creation",
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
        print("Testing Jira connections...")
        results = await test_all_jira_services()
        
        print(f"\n=== Jira Test Results ===")
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
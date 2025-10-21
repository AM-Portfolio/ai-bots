"""Test GitHub connection and operations"""
import asyncio
import logging
from typing import Dict, Any
from shared.config import settings

logger = logging.getLogger(__name__)


async def test_github_connection() -> Dict[str, Any]:
    """Test GitHub connection"""
    result = {
        "service": "GitHub API",
        "configured": bool(settings.github_token),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "GitHub token not configured"
        return result
    
    try:
        # Import GitHub SDK
        from github import Github
        
        # Test connection
        g = Github(settings.github_token)
        user = g.get_user()
        
        result["connection"] = True
        result["details"] = {
            "username": user.login,
            "name": user.name,
            "email": user.email,
            "public_repos": user.public_repos,
            "private_repos": user.total_private_repos,
            "rate_limit": g.get_rate_limit().core.remaining
        }
        
    except ImportError as e:
        result["error"] = f"PyGithub not installed: {e}"
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_github_organization() -> Dict[str, Any]:
    """Test GitHub organization access"""
    result = {
        "service": "GitHub Organization",
        "configured": bool(settings.github_token and settings.github_org),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "GitHub token or organization not configured"
        return result
    
    try:
        # Import GitHub SDK
        from github import Github
        
        # Test organization access
        g = Github(settings.github_token)
        org = g.get_organization(settings.github_org)
        
        # Get some org details
        repos = list(org.get_repos())
        members = list(org.get_members())
        
        result["connection"] = True
        result["details"] = {
            "organization": settings.github_org,
            "name": org.name,
            "description": org.description,
            "public_repos": org.public_repos,
            "total_repos": len(repos),
            "members_count": len(members),
            "sample_repos": [repo.name for repo in repos[:5]]  # Show first 5 repos
        }
        
    except ImportError as e:
        result["error"] = f"PyGithub not installed: {e}"
    except Exception as e:
        result["error"] = f"Organization access failed: {e}"
    
    return result


async def test_github_repository_access() -> Dict[str, Any]:
    """Test access to current repository"""
    result = {
        "service": "GitHub Repository Access",
        "configured": bool(settings.github_token and settings.github_org),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "GitHub token or organization not configured"
        return result
    
    try:
        # Import GitHub SDK
        from github import Github
        
        # Test repository access
        g = Github(settings.github_token)
        repo_name = f"{settings.github_org}/ai-bots"
        repo = g.get_repo(repo_name)
        
        # Get repository details
        branches = list(repo.get_branches())
        commits = list(repo.get_commits()[:5])  # Last 5 commits
        
        result["connection"] = True
        result["details"] = {
            "repository": repo_name,
            "full_name": repo.full_name,
            "description": repo.description,
            "private": repo.private,
            "default_branch": repo.default_branch,
            "branches_count": len(branches),
            "recent_commits": [{"sha": c.sha[:7], "message": c.commit.message.split('\n')[0]} for c in commits]
        }
        
    except ImportError as e:
        result["error"] = f"PyGithub not installed: {e}"
    except Exception as e:
        result["error"] = f"Repository access failed: {e}"
    
    return result


async def test_all_github_services() -> Dict[str, Any]:
    """Test all GitHub services"""
    logger.info("Testing GitHub services...")
    
    results = {}
    
    # Test basic connection
    results["connection"] = await test_github_connection()
    
    # Test organization (only if connection works)
    if results["connection"]["connection"]:
        results["organization"] = await test_github_organization()
        results["repository"] = await test_github_repository_access()
    else:
        results["organization"] = {
            "service": "GitHub Organization",
            "configured": False,
            "connection": False,
            "error": "Skipped due to connection failure",
            "details": {}
        }
        results["repository"] = {
            "service": "GitHub Repository Access",
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
        print("Testing GitHub connections...")
        results = await test_all_github_services()
        
        print(f"\n=== GitHub Test Results ===")
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
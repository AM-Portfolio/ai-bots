"""Test Azure connections and services"""
import asyncio
import logging
from typing import Dict, Any, Optional
from shared.config import settings

logger = logging.getLogger(__name__)


async def test_azure_key_vault() -> Dict[str, Any]:
    """Test Azure Key Vault connection"""
    result = {
        "service": "Azure Key Vault",
        "configured": bool(settings.azure_key_vault_url and settings.azure_tenant_id),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Azure Key Vault credentials not configured"
        return result
    
    try:
        # Import Azure SDK modules
        from azure.keyvault.secrets import SecretClient
        from azure.identity import DefaultAzureCredential
        
        # Test connection
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=settings.azure_key_vault_url, credential=credential)
        
        # Try to list secrets (this will verify connection)
        secrets = client.list_properties_of_secrets()
        secret_count = len(list(secrets))
        
        result["connection"] = True
        result["details"] = {
            "vault_url": settings.azure_key_vault_url,
            "secret_count": secret_count
        }
        
    except ImportError as e:
        result["error"] = f"Azure SDK not installed: {e}"
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_azure_openai() -> Dict[str, Any]:
    """Test Azure OpenAI connection"""
    result = {
        "service": "Azure OpenAI",
        "configured": bool(settings.azure_openai_endpoint and settings.azure_openai_api_key),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Azure OpenAI credentials not configured"
        return result
    
    try:
        # Import OpenAI module
        from openai import AzureOpenAI
        
        # Test connection
        client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version
        )
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        result["connection"] = True
        result["details"] = {
            "endpoint": settings.azure_openai_endpoint,
            "deployment": settings.azure_openai_deployment_name,
            "api_version": settings.azure_openai_api_version,
            "test_response": response.choices[0].message.content if response.choices else None
        }
        
    except ImportError as e:
        result["error"] = f"OpenAI SDK not installed: {e}"
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_all_azure_services() -> Dict[str, Any]:
    """Test all Azure services"""
    logger.info("Testing Azure services...")
    
    results = {}
    
    # Test Key Vault
    results["key_vault"] = await test_azure_key_vault()
    
    # Test OpenAI
    results["openai"] = await test_azure_openai()
    
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
        print("Testing Azure connections...")
        results = await test_all_azure_services()
        
        print(f"\n=== Azure Services Test Results ===")
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
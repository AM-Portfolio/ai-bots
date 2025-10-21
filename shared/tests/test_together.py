"""Test Together AI connection and models"""
import asyncio
import logging
from typing import Dict, Any
from shared.config import settings

logger = logging.getLogger(__name__)


async def test_together_ai() -> Dict[str, Any]:
    """Test Together AI connection"""
    result = {
        "service": "Together AI",
        "configured": bool(settings.together_api_key),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Together AI API key not configured"
        return result
    
    try:
        # Import Together SDK
        import together
        
        # Set API key
        together.api_key = settings.together_api_key
        
        # Test connection with a simple completion
        response = together.Complete.create(
            prompt="Hello",
            model=settings.together_model,
            max_tokens=10,
            temperature=0.1
        )
        
        result["connection"] = True
        result["details"] = {
            "model": settings.together_model,
            "api_key_prefix": settings.together_api_key[:8] + "..." if settings.together_api_key else None,
            "test_response": response.get("output", {}).get("choices", [{}])[0].get("text", "").strip() if response else None
        }
        
    except ImportError as e:
        result["error"] = f"Together SDK not installed: {e}"
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_together_models() -> Dict[str, Any]:
    """Test available Together AI models"""
    result = {
        "service": "Together AI Models",
        "configured": bool(settings.together_api_key),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Together AI API key not configured"
        return result
    
    try:
        # Import Together SDK
        import together
        
        # Set API key
        together.api_key = settings.together_api_key
        
        # Get available models
        models = together.Models.list()
        
        # Filter for text generation models
        text_models = [m for m in models if m.get("type") == "chat" or "instruct" in m.get("name", "").lower()]
        
        result["connection"] = True
        result["details"] = {
            "total_models": len(models),
            "text_models": len(text_models),
            "current_model": settings.together_model,
            "sample_models": [m.get("name") for m in text_models[:5]]  # Show first 5
        }
        
    except ImportError as e:
        result["error"] = f"Together SDK not installed: {e}"
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_all_together_services() -> Dict[str, Any]:
    """Test all Together AI services"""
    logger.info("Testing Together AI services...")
    
    results = {}
    
    # Test basic connection
    results["connection"] = await test_together_ai()
    
    # Test models (only if connection works)
    if results["connection"]["connection"]:
        results["models"] = await test_together_models()
    else:
        results["models"] = {
            "service": "Together AI Models",
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
        print("Testing Together AI connections...")
        results = await test_all_together_services()
        
        print(f"\n=== Together AI Test Results ===")
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
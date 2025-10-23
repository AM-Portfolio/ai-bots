"""
Test Azure Chat Completion Configuration
Tests the unified chat completion configuration with gpt-4.1-mini
"""

import asyncio
import sys
from shared.config import settings
from shared.azure_services.model_deployment_service import AzureModelDeploymentService


async def test_chat_completion_config():
    """Test chat completion configuration"""
    
    print("\n" + "="*60)
    print("AZURE CHAT COMPLETION CONFIGURATION TEST")
    print("="*60 + "\n")
    
    # Display configuration
    print("📋 Current Configuration:")
    print(f"   • Endpoint: {settings.azure_openai_endpoint}")
    print(f"   • Default Chat Model: {settings.azure_chat_model}")
    print(f"   • Chat API Version: {settings.azure_chat_api_version}")
    print(f"   • Model Router: {settings.azure_model_router_deployment}")
    print()
    
    # Initialize service
    service = AzureModelDeploymentService()
    
    if not service.is_available():
        print("❌ Service not available")
        return False
    
    # Get deployment info
    info = await service.get_deployment_info()
    print("🔧 Deployment Information:")
    for deployment_name, deployment_info in info["deployments"].items():
        print(f"\n   {deployment_name}:")
        print(f"      Name: {deployment_info['name']}")
        if 'url' in deployment_info:
            print(f"      URL: {deployment_info['url']}")
        print(f"      Capabilities: {', '.join(deployment_info['capabilities'])}")
    print()
    
    # Test messages
    test_messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Respond with exactly 'Hello, World!' and nothing else."
        },
        {
            "role": "user",
            "content": "Say hello"
        }
    ]
    
    # Test 1: Default chat model (gpt-4.1-mini)
    print("\n" + "-"*60)
    print("TEST 1: Default Chat Model (gpt-4.1-mini)")
    print("-"*60)
    
    try:
        response = await service.chat_completion(
            messages=test_messages,
            temperature=0.5,
            max_tokens=50
        )
        print(f"✅ Success!")
        print(f"   Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Model Router (if configured)
    if settings.azure_model_router_deployment:
        print("\n" + "-"*60)
        print("TEST 2: Model Router Deployment")
        print("-"*60)
        
        try:
            response = await service.chat_with_model_router(
                messages=test_messages,
                temperature=0.5,
                max_tokens=50
            )
            print(f"✅ Success!")
            print(f"   Response: {response}")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # Test 3: Explicit model override
    print("\n" + "-"*60)
    print("TEST 3: Explicit Model Override")
    print("-"*60)
    
    try:
        # Try with explicit model name
        response = await service.chat_completion(
            messages=test_messages,
            temperature=0.5,
            max_tokens=50,
            model="gpt-4.1-mini"
        )
        print(f"✅ Success!")
        print(f"   Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_chat_completion_config())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

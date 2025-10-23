"""
Test LLM Provider Auto-Detection and Smart Fallback

This script demonstrates the new intelligent provider selection:
- Auto-detects configured providers from .env
- Uses single provider exclusively if only one configured
- Enables fallback only when both providers are configured
- Raises error if no providers are configured
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.llm_providers.factory import get_llm_client, LLMFactory
from shared.config import settings
from shared.logger import get_logger

logger = get_logger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_provider_detection():
    """Test provider detection based on .env configuration"""
    print_section("1. PROVIDER DETECTION")
    
    configured = LLMFactory.detect_configured_providers(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_api_key=settings.azure_openai_api_key,
        together_api_key=settings.together_api_key
    )
    
    print("📋 Configured Providers:")
    print(f"   • Azure OpenAI:  {'✅ Yes' if configured['azure'] else '❌ No'}")
    if configured['azure']:
        print(f"      - Endpoint: {settings.azure_openai_endpoint}")
        print(f"      - Deployment: {settings.azure_openai_deployment_name}")
    
    print(f"   • Together AI:   {'✅ Yes' if configured['together'] else '❌ No'}")
    if configured['together']:
        print(f"      - Model: {settings.together_model}")
    
    num_configured = sum(configured.values())
    print(f"\n📊 Total Configured: {num_configured}")
    
    if num_configured == 0:
        print("   ⚠️  No providers configured - will raise error")
    elif num_configured == 1:
        provider_name = "Azure" if configured['azure'] else "Together AI"
        print(f"   ℹ️  Single provider mode - {provider_name} only (no fallback)")
    else:
        print(f"   ✅ Multiple providers - fallback enabled")
    
    return configured, num_configured


def test_auto_mode(num_configured: int):
    """Test auto-detection mode"""
    print_section("2. AUTO-DETECTION MODE")
    
    if num_configured == 0:
        print("⚠️  Skipping - no providers configured")
        return
    
    print("🔍 Testing provider_type='auto'...")
    
    try:
        client = get_llm_client(
            provider_type="auto",
            azure_endpoint=settings.azure_openai_endpoint,
            azure_api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_deployment_name,
            azure_api_version=settings.azure_openai_api_version,
            together_api_key=settings.together_api_key,
            together_model=settings.together_model
        )
        
        provider_name = type(client).__name__
        print(f"\n✅ Auto-detection successful!")
        print(f"   • Selected Provider: {provider_name}")
        print(f"   • Is Available: {client.is_available()}")
        
    except Exception as e:
        print(f"\n❌ Auto-detection failed: {e}")


def test_azure_primary(configured: dict):
    """Test Azure as primary provider"""
    print_section("3. AZURE PRIMARY MODE")
    
    if not configured['azure']:
        print("⚠️  Skipping - Azure not configured")
        return
    
    print("🔍 Testing provider_type='azure'...")
    
    try:
        client = get_llm_client(
            provider_type="azure",
            azure_endpoint=settings.azure_openai_endpoint,
            azure_api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_deployment_name,
            azure_api_version=settings.azure_openai_api_version,
            together_api_key=settings.together_api_key,
            together_model=settings.together_model
        )
        
        provider_name = type(client).__name__
        print(f"\n✅ Azure mode successful!")
        print(f"   • Active Provider: {provider_name}")
        print(f"   • Is Available: {client.is_available()}")
        
        if configured['together']:
            print(f"   • Fallback Available: Yes (Together AI)")
        else:
            print(f"   • Fallback Available: No (Azure only)")
        
    except Exception as e:
        print(f"\n❌ Azure mode failed: {e}")


def test_together_primary(configured: dict):
    """Test Together AI as primary provider"""
    print_section("4. TOGETHER AI PRIMARY MODE")
    
    if not configured['together']:
        print("⚠️  Skipping - Together AI not configured")
        return
    
    print("🔍 Testing provider_type='together'...")
    
    try:
        client = get_llm_client(
            provider_type="together",
            azure_endpoint=settings.azure_openai_endpoint,
            azure_api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_deployment_name,
            azure_api_version=settings.azure_openai_api_version,
            together_api_key=settings.together_api_key,
            together_model=settings.together_model
        )
        
        provider_name = type(client).__name__
        print(f"\n✅ Together AI mode successful!")
        print(f"   • Active Provider: {provider_name}")
        print(f"   • Is Available: {client.is_available()}")
        
        if configured['azure']:
            print(f"   • Fallback Available: Yes (Azure OpenAI)")
        else:
            print(f"   • Fallback Available: No (Together AI only)")
        
    except Exception as e:
        print(f"\n❌ Together AI mode failed: {e}")


def test_no_providers():
    """Test error handling when no providers are configured"""
    print_section("5. NO PROVIDERS CONFIGURED (ERROR TEST)")
    
    print("🔍 Testing with no credentials...")
    
    try:
        client = get_llm_client(
            provider_type="auto",
            azure_endpoint=None,
            azure_api_key=None,
            together_api_key=None
        )
        print(f"\n❌ Should have raised error but got: {type(client).__name__}")
        
    except ValueError as e:
        print(f"\n✅ Correctly raised ValueError:")
        print(f"   {e}")
    except Exception as e:
        print(f"\n⚠️  Raised unexpected error: {e}")


def test_chat_completion(configured: dict, num_configured: int):
    """Test actual chat completion with selected provider"""
    print_section("6. CHAT COMPLETION TEST")
    
    if num_configured == 0:
        print("⚠️  Skipping - no providers configured")
        return
    
    print("💬 Testing chat completion with auto-detection...")
    
    try:
        from shared.llm import llm_client
        
        # Simple test message
        messages = [
            {"role": "user", "content": "Say 'Hello from AI!' in exactly 3 words."}
        ]
        
        print("\n📤 Sending message: 'Say Hello from AI! in exactly 3 words.'")
        
        # Use asyncio to run the async function
        import asyncio
        
        async def run_test():
            response = await llm_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=50
            )
            return response
        
        response = asyncio.run(run_test())
        
        if response:
            print(f"\n📥 Response received:")
            print(f"   {response}")
            print(f"\n✅ Chat completion successful!")
        else:
            print(f"\n⚠️  No response received")
        
    except Exception as e:
        print(f"\n❌ Chat completion failed: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  🧪 LLM PROVIDER AUTO-DETECTION & SMART FALLBACK TEST")
    print("="*70)
    
    # Test 1: Provider detection
    configured, num_configured = test_provider_detection()
    
    # Test 2: Auto mode
    test_auto_mode(num_configured)
    
    # Test 3: Azure primary
    test_azure_primary(configured)
    
    # Test 4: Together primary
    test_together_primary(configured)
    
    # Test 5: No providers (error test)
    test_no_providers()
    
    # Test 6: Chat completion
    test_chat_completion(configured, num_configured)
    
    # Summary
    print_section("SUMMARY")
    
    print("📊 Test Results:")
    print(f"   • Providers Configured: {num_configured}")
    print(f"   • Azure: {'✅' if configured['azure'] else '❌'}")
    print(f"   • Together AI: {'✅' if configured['together'] else '❌'}")
    
    if num_configured == 0:
        print("\n⚠️  Action Required:")
        print("   Configure at least one provider in .env:")
        print("   - Azure: AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY")
        print("   - Together AI: TOGETHER_API_KEY")
    elif num_configured == 1:
        provider = "Azure" if configured['azure'] else "Together AI"
        print(f"\n✅ Single Provider Mode:")
        print(f"   Using {provider} exclusively (no fallback)")
    else:
        print(f"\n✅ Multi-Provider Mode:")
        print(f"   Both providers configured - smart fallback enabled")
    
    print("\n" + "="*70)
    print("  ✅ All tests completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

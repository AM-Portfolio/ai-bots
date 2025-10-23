"""
Test Provider Selection

Verify that Azure is used as primary provider by default
"""

import asyncio
from shared.config import settings
from shared.llm_providers.factory import get_llm_client


async def test_provider_selection():
    """Test which provider is selected"""
    
    print("\n" + "="*70)
    print("PROVIDER SELECTION TEST")
    print("="*70 + "\n")
    
    # Check configuration
    print("📋 Configuration:")
    print(f"   • LLM_PROVIDER: {settings.llm_provider}")
    print(f"   • Azure Endpoint: {settings.azure_openai_endpoint}")
    print(f"   • Azure API Key: {'***' + settings.azure_openai_api_key[-4:] if settings.azure_openai_api_key else 'Not set'}")
    print(f"   • Together API Key: {'***' + settings.together_api_key[-4:] if settings.together_api_key else 'Not set'}")
    print()
    
    # Get LLM client with settings
    print("🔍 Getting LLM client...")
    client = get_llm_client(
        provider_type=settings.llm_provider,
        azure_endpoint=settings.azure_openai_endpoint,
        azure_api_key=settings.azure_openai_api_key or settings.azure_openai_key,
        azure_deployment=settings.azure_openai_deployment_name,
        azure_api_version=settings.azure_openai_api_version,
        together_api_key=settings.together_api_key,
        together_model=settings.together_model
    )
    
    # Check provider type
    provider_name = client.__class__.__name__
    print(f"\n✅ Selected Provider: {provider_name}")
    print(f"   • Available: {client.is_available()}")
    
    if "Azure" in provider_name:
        print(f"   • ✅ Using Azure OpenAI (as expected)")
    elif "Together" in provider_name:
        print(f"   • ⚠️  Using Together AI (should be Azure)")
    
    # Test a simple chat completion
    print("\n" + "-"*70)
    print("Testing Chat Completion")
    print("-"*70)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Reply with exactly 'Azure' if you are Azure OpenAI, or 'Together' if you are Together AI."},
        {"role": "user", "content": "Which provider are you?"}
    ]
    
    try:
        response = await client.chat_completion(
            messages=messages,
            temperature=0,
            max_tokens=10
        )
        print(f"\n✅ Response: {response}")
        
        if "Azure" in response or "gpt" in response.lower():
            print("   • ✅ Confirmed: Azure OpenAI is being used")
        elif "Together" in response or "llama" in response.lower():
            print("   • ⚠️  Warning: Together AI is being used instead of Azure")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_provider_selection())

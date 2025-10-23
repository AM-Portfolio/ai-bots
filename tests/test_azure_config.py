#!/usr/bin/env python3
"""
Test script to validate Azure AI configuration from .env file

This script tests:
1. Configuration loading from .env
2. Azure service initialization
3. Configuration validation and reporting using the separate validator
"""

import logging
import asyncio
from shared.azure_services.azure_ai_manager import azure_ai_manager
from shared.azure_services.azure_config_validator import azure_config_validator
from shared.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_configuration_loading():
    """Test that configuration values are loaded from .env"""
    print("\n🔧 Testing Configuration Loading from .env")
    print("=" * 50)
    
    # Test Azure Speech configuration
    print(f"Azure Speech Key present: {bool(settings.azure_speech_key)}")
    print(f"Azure Speech Region: {settings.azure_speech_region}")
    print(f"Azure Speech Language: {settings.azure_speech_lang}")
    
    # Test Azure Translation configuration (with fallbacks)
    translation_key = settings.azure_translation_key or settings.azure_translator_key
    translation_region = settings.azure_translation_region or settings.azure_translator_region
    print(f"Azure Translation Key present: {bool(translation_key)}")
    print(f"Azure Translation Region: {translation_region}")
    
    # Test Azure OpenAI configuration
    openai_key = settings.azure_openai_api_key or settings.azure_openai_key
    print(f"Azure OpenAI Endpoint: {settings.azure_openai_endpoint}")
    print(f"Azure OpenAI Key present: {bool(openai_key)}")
    print(f"Azure OpenAI API Version: {settings.azure_openai_api_version}")
    
    # Test Model Deployment configuration
    print(f"GPT-4o Transcribe Deployment: {settings.azure_gpt4o_transcribe_deployment}")
    print(f"Model Router Deployment: {settings.azure_model_router_deployment}")
    print(f"GPT Audio Mini Deployment: {settings.azure_gpt_audio_mini_deployment}")


def test_config_validator():
    """Test the separate configuration validator"""
    print("\n🔍 Testing Configuration Validator")
    print("=" * 50)
    
    # Test validation
    validation = azure_config_validator.validate_configuration()
    print(f"Configuration valid: {'✅' if validation['is_valid'] else '❌'}")
    
    if validation['missing_config']:
        print(f"Missing config: {', '.join(validation['missing_config'])}")
    
    if validation['warnings']:
        print(f"Warnings: {', '.join(validation['warnings'])}")
    
    # Test missing variables check
    missing_check = azure_config_validator.check_missing_variables()
    print(f"Missing variables: {len(missing_check['missing_variables'])}")
    
    return validation


def test_service_initialization():
    """Test Azure service initialization"""
    print("\n🚀 Testing Service Initialization")
    print("=" * 50)
    
    # Get service status
    status = azure_ai_manager.get_service_status()
    
    print("Service Availability:")
    print(f"  Speech Service: {'✅' if status['service_endpoints']['speech']['available'] else '❌'}")
    print(f"  Translation Service: {'✅' if status['service_endpoints']['translation']['available'] else '❌'}")
    print(f"  Model Deployments: {'✅' if status['model_deployments']['available'] else '❌'}")
    
    return status


async def test_full_configuration():
    """Test full configuration and service status"""
    print("\n🧪 Testing Full Configuration")
    print("=" * 50)
    
    # Get comprehensive test results
    results = await azure_ai_manager.test_all_services()
    
    print("\nConfiguration from .env:")
    config = results['configuration_from_env']
    
    print(f"  Azure Speech configured: {'✅' if config['azure_speech']['configured'] else '❌'}")
    print(f"  Azure Translation configured: {'✅' if config['azure_translation']['configured'] else '❌'}")
    print(f"  Azure OpenAI configured: {'✅' if config['azure_openai']['configured'] else '❌'}")
    print(f"  Azure AI Services configured: {'✅' if config['azure_ai_services']['configured'] else '❌'}")
    
    print(f"\nAvailable Workflows: {', '.join(results['workflows_available']) if results['workflows_available'] else 'None'}")
    
    return results


async def main():
    """Main test function"""
    print("🔍 Azure AI Configuration Test (with Separate Validator)")
    print("=" * 60)
    
    try:
        # Test 1: Configuration loading
        test_configuration_loading()
        
        # Test 2: Configuration validator
        test_config_validator()
        
        # Test 3: Service initialization
        test_service_initialization()
        
        # Test 4: Full configuration test
        await test_full_configuration()
        
        print("\n✅ Configuration test completed successfully!")
        print("\nArchitecture Benefits:")
        print("• Validation logic is separated from Azure AI Manager")
        print("• Azure AI Manager focuses on service coordination")
        print("• Configuration validator can be reused independently")
        print("• Better separation of concerns and maintainability")
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        logger.exception("Configuration test error")


if __name__ == "__main__":
    asyncio.run(main())
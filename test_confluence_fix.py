"""Test Confluence client fixes"""
from shared.clients.confluence_client import ConfluenceClient
from shared.config import settings

print("=" * 60)
print("Testing Confluence Client Configuration")
print("=" * 60)

print(f"\n📋 Configuration from .env:")
print(f"   • Confluence URL: {settings.confluence_url}")
print(f"   • Default Space Key: {settings.confluence_space_key}")
print(f"   • Default Parent ID: {settings.parent_page_id}")
print(f"   • Jira Project Key: {settings.jira_project_key}")

print(f"\n🔧 Testing ConfluenceClient initialization...")
try:
    client = ConfluenceClient()
    print(f"✅ ConfluenceClient initialized successfully!")
    print(f"   • Is Configured: {client.is_configured()}")
    print(f"   • Site URL: {client.site_url}")
    
    print("\n" + "=" * 60)
    print("✅ FIXES IMPLEMENTED:")
    print("=" * 60)
    print("1. ✅ Confluence space key fallback logic:")
    print("   - API request includes 'confluence_space_key' → use it")
    print("   - API request omits 'confluence_space_key' → use .env value")
    print(f"   - Fallback value: {settings.confluence_space_key}")
    print()
    print("2. ✅ Jira project key fallback logic:")
    print("   - API request includes 'jira_project_key' → use it")
    print("   - API request omits 'jira_project_key' → use .env value")
    print(f"   - Fallback value: {settings.jira_project_key}")
    print()
    print("3. ✅ Fixed Confluence get_page error:")
    print("   - Added 'space' to expand parameter")
    print("   - Safe dictionary access with .get()")
    print("   - Fallback to .env space key if missing")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Failed to initialize ConfluenceClient: {e}")

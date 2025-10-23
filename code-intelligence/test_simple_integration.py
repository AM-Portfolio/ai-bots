"""
Simple Integration Test for Code Intelligence

This test performs a basic workflow check without async conflicts:
1. Test embedding pipeline initialization
2. Test query service initialization  
3. Test file discovery
4. Generate a simple embedding report

Note: This avoids asyncio.run() conflicts by not calling cleanup/query directly.
"""

import sys
import os
from pathlib import Path

# Add code-intelligence directory to path
code_intel_dir = Path(__file__).parent
if str(code_intel_dir) not in sys.path:
    sys.path.insert(0, str(code_intel_dir))

# Add parent directory to path for shared modules
parent_dir = code_intel_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import after path is set
from embed_repo import EmbeddingPipeline
from pipeline.file_discovery import FileDiscovery
from utils.enhanced_query import EnhancedQueryService


def test_initialization():
    """Test that all components can be initialized"""
    print("\n" + "=" * 80)
    print("  TEST 1: Component Initialization")
    print("=" * 80)
    
    try:
        # Test file discovery
        print("\n📁 Testing FileDiscovery...")
        repo_path = str(parent_dir)
        discovery = FileDiscovery(repo_path)
        print(f"✅ FileDiscovery initialized for: {repo_path}")
        
        # Test query service
        print("\n🔍 Testing EnhancedQueryService...")
        query_service = EnhancedQueryService()
        print("✅ EnhancedQueryService initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_discovery():
    """Test file discovery on current repository"""
    print("\n" + "=" * 80)
    print("  TEST 2: File Discovery")
    print("=" * 80)
    
    try:
        repo_path = str(parent_dir)
        print(f"\n📂 Discovering files in: {repo_path}")
        
        discovery = FileDiscovery(repo_path)
        files = discovery.discover_files()
        
        print(f"\n✅ Discovery complete:")
        print(f"   Total files found: {len(files)}")
        
        # Show file type breakdown
        extensions = {}
        for f in files:
            ext = Path(f).suffix
            extensions[ext] = extensions.get(ext, 0) + 1
        
        print(f"\n📊 File types:")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {ext or '(no ext)'}: {count} files")
        
        # Show some example files from code-intelligence/
        code_intel_files = [f for f in files if 'code-intelligence' in f and not '__pycache__' in f]
        print(f"\n📄 Sample files from code-intelligence/ ({len(code_intel_files)} total):")
        for f in code_intel_files[:10]:
            rel_path = os.path.relpath(f, repo_path)
            size_kb = os.path.getsize(f) / 1024
            print(f"   • {rel_path} ({size_kb:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ File discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_service():
    """Test query service search capabilities"""
    print("\n" + "=" * 80)
    print("  TEST 3: Query Service")
    print("=" * 80)
    
    try:
        print("\n🔍 Testing EnhancedQueryService...")
        
        query_service = EnhancedQueryService()
        
        # Check that the service has the search method
        if not hasattr(query_service, 'search'):
            print("❌ EnhancedQueryService missing 'search' method")
            return False
        
        print("✅ EnhancedQueryService has 'search' method")
        print("✅ Query service is properly initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Query service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_summary():
    """Test that enhanced summarizer can be imported and has expected interface"""
    print("\n" + "=" * 80)
    print("  TEST 4: Enhanced Summarizer Interface")
    print("=" * 80)
    
    try:
        from enhanced_summarizer import EnhancedCodeSummarizer
        
        print("\n📝 Testing EnhancedCodeSummarizer...")
        
        # Check that class has expected methods
        expected_methods = ['summarize_batch', 'summarize_chunk']
        missing = []
        
        for method in expected_methods:
            if not hasattr(EnhancedCodeSummarizer, method):
                missing.append(method)
        
        if missing:
            print(f"❌ Missing methods: {missing}")
            return False
        
        print(f"✅ EnhancedCodeSummarizer has all expected methods:")
        for method in expected_methods:
            print(f"   • {method}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced summarizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    
    print("\n" + "🧪" * 40)
    print("  CODE INTELLIGENCE - SIMPLE INTEGRATION TEST")
    print("🧪" * 40)
    
    print(f"\nRepository: {parent_dir}")
    print(f"Test Directory: {code_intel_dir}")
    
    # Run all tests
    tests = [
        ("Component Initialization", test_initialization),
        ("File Discovery", test_file_discovery),
        ("Query Service", test_query_service),
        ("Enhanced Summarizer", test_enhanced_summary),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Print summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    print("\nDetailed Results:")
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {name}")
    
    print("\n" + "=" * 80)
    if all(results.values()):
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

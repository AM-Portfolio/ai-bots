"""
GitHub Integration Test for Code Intelligence (CLI-based)

This test performs a complete workflow with a real GitHub repository using CLI commands.
This avoids asyncio event loop conflicts by using subprocess to call the CLI.

Workflow:
1. Cleanup any existing test data
2. Embed repository from GitHub
3. Query the embedded code
4. Get statistics
5. Cleanup test data

Usage:
    python test_github_cli.py owner/repo [max_files]
    
Example:
    python test_github_cli.py octocat/Hello-World 3
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any

# Add code-intelligence directory to path
code_intel_dir = Path(__file__).parent
parent_dir = code_intel_dir.parent


class GitHubCLITest:
    """Integration test using CLI commands to avoid async conflicts"""
    
    def __init__(self, repo_name: str, max_files: int = 5):
        """
        Initialize test with GitHub repository.
        
        Args:
            repo_name: GitHub repository in format "owner/repo"
            max_files: Maximum number of files to process (default: 5)
        """
        self.repo_name = repo_name
        self.max_files = max_files
        self.collection_name = f"test_{repo_name.replace('/', '_')}"
        self.main_py = str(code_intel_dir / "main.py")
        self.results = {}
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)
    
    def run_cli_command(self, args: list) -> tuple[bool, str]:
        """
        Run a CLI command and return success status and output.
        
        Args:
            args: Command arguments
            
        Returns:
            Tuple of (success, output)
        """
        try:
            cmd = ["python", self.main_py] + args
            print(f"   Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(parent_dir),
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "Command timed out after 5 minutes"
        except Exception as e:
            return False, f"Command failed: {e}"
    
    def test_cleanup_before(self) -> bool:
        """Test 1: Cleanup any existing test data"""
        self.print_header("TEST 1: Initial Cleanup")
        
        try:
            print(f"\n🧹 Cleaning up existing collection: {self.collection_name}")
            
            success, output = self.run_cli_command([
                "cleanup",
                "--collection", self.collection_name,
                "--force"
            ])
            
            # Cleanup failure is OK if collection doesn't exist
            if "not found" in output.lower() or "does not exist" in output.lower():
                print(f"⚠️  Collection doesn't exist yet (normal for first run)")
                return True
            elif success:
                print(f"✅ Cleanup complete")
                return True
            else:
                print(f"⚠️  Cleanup warning (non-critical)")
                return True  # Don't fail on cleanup
                
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
            return True  # Not critical
    
    def test_embed_repository(self) -> bool:
        """Test 2: Create embeddings from GitHub repository"""
        self.print_header("TEST 2: Create Embeddings from GitHub")
        
        try:
            print(f"\n📝 Embedding repository: {self.repo_name}")
            print(f"   Max files: {self.max_files}")
            print(f"   Collection: {self.collection_name}")
            
            success, output = self.run_cli_command([
                "embed",
                "--github-repo", self.repo_name,
                "--collection", self.collection_name,
                "--max-files", str(self.max_files),
                "--force-reindex"
            ])
            
            if success:
                print(f"\n✅ Embedding complete")
                # Try to extract statistics from output
                if "chunks" in output.lower():
                    lines = output.split('\n')
                    for line in lines:
                        if "processed" in line.lower() or "chunks" in line.lower() or "embeddings" in line.lower():
                            print(f"   {line.strip()}")
                return True
            else:
                print(f"\n❌ Embedding failed")
                # Print relevant error lines
                error_lines = [line for line in output.split('\n') if 'error' in line.lower() or 'failed' in line.lower()]
                for line in error_lines[:5]:  # Show first 5 error lines
                    print(f"   {line.strip()}")
                return False
                
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            return False
    
    def test_query_code(self) -> bool:
        """Test 3: Query the embedded code"""
        self.print_header("TEST 3: Query Embedded Code")
        
        try:
            test_queries = [
                "main function or entry point",
                "class definitions",
                "configuration or settings"
            ]
            
            print(f"\n🔍 Running {len(test_queries)} test queries...")
            
            all_success = True
            for i, query in enumerate(test_queries, 1):
                print(f"\n📋 Query {i}: '{query}'")
                
                success, output = self.run_cli_command([
                    "query",
                    query,
                    "--collection", self.collection_name,
                    "--limit", "3"
                ])
                
                if success:
                    # Check if results were found
                    if "found 0 results" in output.lower() or "no results" in output.lower():
                        print(f"   ⚠️  No results found (may be due to parsing issues)")
                    else:
                        print(f"   ✅ Query completed")
                        # Show first result snippet
                        lines = output.split('\n')
                        for idx, line in enumerate(lines):
                            if "result" in line.lower() and idx < len(lines) - 3:
                                for j in range(min(3, len(lines) - idx)):
                                    print(f"   {lines[idx + j].strip()}")
                                break
                else:
                    print(f"   ❌ Query failed")
                    all_success = False
            
            return all_success
            
        except Exception as e:
            print(f"❌ Query testing failed: {e}")
            return False
    
    def test_get_stats(self) -> bool:
        """Test 4: Get collection statistics"""
        self.print_header("TEST 4: Get Statistics")
        
        try:
            print(f"\n📊 Retrieving statistics...")
            
            success, output = self.run_cli_command([
                "health"
            ])
            
            if success:
                print(f"\n✅ Statistics retrieved:")
                # Show collection info
                lines = output.split('\n')
                for line in lines:
                    if self.collection_name in line or "collection" in line.lower() or "vectors" in line.lower():
                        print(f"   {line.strip()}")
                return True
            else:
                print(f"❌ Stats retrieval failed")
                return False
                
        except Exception as e:
            print(f"❌ Stats retrieval failed: {e}")
            return False
    
    def test_cleanup_after(self) -> bool:
        """Test 5: Final cleanup"""
        self.print_header("TEST 5: Final Cleanup")
        
        try:
            print(f"\n🧹 Cleaning up test collection: {self.collection_name}")
            
            success, output = self.run_cli_command([
                "cleanup",
                "--collection", self.collection_name,
                "--force"
            ])
            
            if success or "success" in output.lower():
                print(f"✅ Cleanup complete")
                print(f"   Collection removed from vector database")
                return True
            else:
                print(f"⚠️  Cleanup completed with warnings")
                return True  # Don't fail on cleanup warnings
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
    
    def run_all_tests(self) -> int:
        """Run all integration tests"""
        
        print("\n" + "🧪" * 40)
        print("  CODE INTELLIGENCE - GITHUB CLI INTEGRATION TEST")
        print("🧪" * 40)
        
        print(f"\nGitHub Repository: {self.repo_name}")
        print(f"Collection Name: {self.collection_name}")
        print(f"Max Files to Process: {self.max_files}")
        print(f"CLI Script: {self.main_py}")
        
        # Define all tests
        tests = [
            ("Cleanup Before", self.test_cleanup_before),
            ("Embed Repository", self.test_embed_repository),
            ("Query Code", self.test_query_code),
            ("Get Statistics", self.test_get_stats),
            ("Cleanup After", self.test_cleanup_after),
        ]
        
        # Run tests
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
        self.print_header("TEST SUMMARY")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"\nTests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        print("\nDetailed Results:")
        for name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {status}: {name}")
        
        print("\n" + "=" * 80)
        if all(results.values()):
            print("✅ ALL TESTS PASSED")
            print("=" * 80)
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            print("   Note: Some failures may be due to known issues:")
            print("   - FallbackParser missing parse() method")
            print("   - Tree-sitter initialization warnings")
            print("   See docs/KNOWN_ISSUES.md for details")
            print("=" * 80)
            return 1


def main():
    """Main entry point"""
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python test_github_cli.py owner/repo [max_files]")
        print("\nExamples:")
        print("  python test_github_cli.py octocat/Hello-World 3")
        print("  python test_github_cli.py microsoft/vscode 5")
        print("  python test_github_cli.py facebook/react 10")
        print("\nThis test uses CLI commands to avoid async event loop conflicts.")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    max_files = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Validate repository name format
    if '/' not in repo_name:
        print(f"❌ Error: Invalid repository format '{repo_name}'")
        print("   Expected format: owner/repo")
        print("   Example: octocat/Hello-World")
        sys.exit(1)
    
    # Run tests
    test = GitHubCLITest(repo_name, max_files)
    exit_code = test.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

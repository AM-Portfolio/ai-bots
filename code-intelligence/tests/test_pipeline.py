"""
Quick test script to verify the embedding pipeline works correctly.

Tests:
1. Rate limiter initialization
2. Parser registry loading
3. Change planner file discovery
4. RepoState caching
5. Component integration
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rate_limiter():
    """Test rate limiter initialization and basic functionality"""
    from rate_limiter import RateLimitController, QuotaType
    
    logger.info("🧪 Testing RateLimitController...")
    
    controller = RateLimitController()
    await controller.start()
    
    # Test async task submission
    async def dummy_task():
        await asyncio.sleep(0.1)
        return "success"
    
    result = await controller.submit(QuotaType.EMBEDDING, dummy_task, priority=5)
    assert result == "success", "Rate limiter task submission failed"
    
    # Check metrics
    metrics = controller.get_metrics(QuotaType.EMBEDDING)
    assert metrics["total_requests"] > 0, "Metrics not tracked"
    
    await controller.stop()
    logger.info("✅ RateLimitController: PASSED")


def test_parser_registry():
    """Test parser registry and language detection"""
    from parsers import parser_registry
    
    logger.info("🧪 Testing ParserRegistry...")
    
    # Check supported languages
    languages = parser_registry.get_supported_languages()
    assert "python" in languages, "Python parser not registered"
    assert "javascript" in languages, "JavaScript parser not registered"
    
    # Check file extension mapping
    extensions = parser_registry.get_supported_extensions()
    assert ".py" in extensions, "Python extension not mapped"
    assert ".js" in extensions, "JavaScript extension not mapped"
    
    # Test parser selection
    parser = parser_registry.get_parser("test.py")
    assert parser.get_language() == "python", "Wrong parser selected for .py"
    
    logger.info("✅ ParserRegistry: PASSED")


def test_repo_state():
    """Test repo state management and caching"""
    from repo_state import RepoState
    import tempfile
    
    logger.info("🧪 Testing RepoState...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        manifest_path = f.name
    
    state = RepoState(manifest_path)
    
    # Test file hashing
    test_file = Path(__file__)
    if test_file.exists():
        hash1 = state.compute_file_hash(str(test_file))
        assert len(hash1) == 64, "Invalid SHA256 hash"
        
        # Test change detection
        is_changed = state.is_file_changed(str(test_file))
        assert is_changed == True, "New file should be marked as changed"
        
        # Update state
        state.update_file_state(
            file_path=str(test_file),
            language="python",
            chunk_count=1,
            status="completed"
        )
        
        # Save and reload
        state.save_manifest()
        state2 = RepoState(manifest_path)
        assert str(test_file) in state2.file_states, "State not persisted"
    
    # Cleanup
    Path(manifest_path).unlink(missing_ok=True)
    
    logger.info("✅ RepoState: PASSED")


def test_change_planner():
    """Test change planner file discovery"""
    from change_planner import ChangePlanner
    
    logger.info("🧪 Testing ChangePlanner...")
    
    planner = ChangePlanner(".")
    
    # Test entry point detection
    test_files = ["main.py", "app.py", "index.js", "src/utils.py"]
    entry_points = planner.detect_entry_points(test_files)
    
    assert "main.py" in entry_points, "main.py should be detected as entry point"
    assert "app.py" in entry_points, "app.py should be detected as entry point"
    assert "index.js" in entry_points, "index.js should be detected as entry point"
    
    logger.info("✅ ChangePlanner: PASSED")


def test_vector_store():
    """Test vector store initialization"""
    from vector_store import VectorStore
    import tempfile
    
    logger.info("🧪 Testing VectorStore...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(
                collection_name="test_collection",
                qdrant_path=tmpdir
            )
            
            # Test health check
            is_healthy = store.health_check()
            assert is_healthy, "Vector store health check failed"
            
            # Test collection info
            info = store.get_collection_info()
            assert "name" in info, "Collection info incomplete"
            
            # Cleanup
            store.delete_collection()
        
        logger.info("✅ VectorStore: PASSED")
    except ImportError as e:
        logger.warning(f"⚠️ VectorStore: SKIPPED (qdrant-client not installed)")


async def run_all_tests():
    """Run all tests"""
    logger.info("="*60)
    logger.info("🎯 Running Code Intelligence Pipeline Tests")
    logger.info("="*60)
    
    try:
        # Async tests
        await test_rate_limiter()
        
        # Sync tests
        test_parser_registry()
        test_repo_state()
        test_change_planner()
        test_vector_store()
        
        logger.info("="*60)
        logger.info("✅ All Tests PASSED")
        logger.info("="*60)
        logger.info("\n📌 Next Steps:")
        logger.info("1. Configure Azure OpenAI credentials in .env")
        logger.info("2. Run: python code-intelligence/embed_repo.py --max-files 10")
        logger.info("3. Check for 429 errors in logs")
        logger.info("4. Verify embeddings in Qdrant")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

"""
Test command handler.
"""

import sys
import logging

logger = logging.getLogger(__name__)


async def cmd_test(args):
    """Handle test command"""
    print("🧪 Running integration tests...")
    try:
        from tests.test_pipeline import main as test_main
        await test_main()
    except ImportError:
        logger.error("Test module not found. Please create tests/test_pipeline.py")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)

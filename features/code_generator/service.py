from typing import List
import logging

from shared.models import AnalysisResult, CodeFix
from shared.llm import llm_client

logger = logging.getLogger(__name__)


async def generate_code_fix(analysis: AnalysisResult) -> List[CodeFix]:
    logger.info(f"Generating code fixes for issue: {analysis.issue_id}")
    
    fixes = []
    
    for suggested_fix in analysis.suggested_fixes:
        test_code = await llm_client.generate_tests(
            code=suggested_fix.fixed_code,
            language="python"
        )
        
        fix_with_test = CodeFix(
            file_path=suggested_fix.file_path,
            original_code=suggested_fix.original_code,
            fixed_code=suggested_fix.fixed_code,
            explanation=suggested_fix.explanation,
            test_code=test_code
        )
        
        fixes.append(fix_with_test)
    
    logger.info(f"Generated {len(fixes)} code fixes with tests")
    return fixes

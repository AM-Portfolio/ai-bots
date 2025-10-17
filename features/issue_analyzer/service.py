from typing import Dict, Any
import logging

from shared.models import AnalysisResult, CodeFix, EnrichedContext
from shared.llm import llm_client

logger = logging.getLogger(__name__)


async def analyze_issue(enriched_context: EnrichedContext) -> AnalysisResult:
    logger.info(f"Analyzing issue: {enriched_context.issue_id}")
    
    context_text = f"""
Issue: {enriched_context.title}
Description: {enriched_context.description}
Severity: {enriched_context.severity}

Code Snippets:
{chr(10).join(enriched_context.code_snippets[:3])}

Logs:
{chr(10).join(enriched_context.logs[:5])}

Stack Traces:
{chr(10).join(enriched_context.stack_traces[:2])}
"""
    
    code_to_analyze = "\n".join(enriched_context.code_snippets[:3])
    
    analysis = await llm_client.analyze_code(
        code=code_to_analyze,
        context=context_text,
        task="diagnose and fix"
    )
    
    if not analysis:
        return AnalysisResult(
            issue_id=enriched_context.issue_id,
            root_cause="Failed to analyze issue",
            affected_components=[],
            suggested_fixes=[],
            confidence_score=0.0
        )
    
    suggested_fixes = []
    if 'fixed_code' in analysis:
        fix = CodeFix(
            file_path="unknown",
            original_code=code_to_analyze,
            fixed_code=analysis.get('fixed_code', ''),
            explanation=analysis.get('explanation', '')
        )
        suggested_fixes.append(fix)
    
    return AnalysisResult(
        issue_id=enriched_context.issue_id,
        root_cause=analysis.get('root_cause', 'Unknown'),
        affected_components=analysis.get('affected_components', []),
        suggested_fixes=suggested_fixes,
        confidence_score=analysis.get('confidence', 0.5),
        analysis_metadata=analysis
    )

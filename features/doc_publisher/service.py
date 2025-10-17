from typing import Optional
import logging

from shared.models import AnalysisResult, DocumentationPage
from shared.clients import ConfluenceClient
from shared.llm import llm_client

logger = logging.getLogger(__name__)


async def publish_documentation(
    analysis: AnalysisResult,
    space_key: str,
    parent_page_id: Optional[str] = None
) -> Optional[str]:
    logger.info(f"Publishing documentation for issue: {analysis.issue_id}")
    
    doc_content = f"""
# Issue Analysis: {analysis.issue_id}

## Root Cause
{analysis.root_cause}

## Affected Components
{', '.join(analysis.affected_components)}

## Suggested Fixes
"""
    
    for i, fix in enumerate(analysis.suggested_fixes, 1):
        doc_content += f"""
### Fix {i}
**File:** {fix.file_path}

**Explanation:** {fix.explanation}

**Code Changes:**
```python
{fix.fixed_code}
```
"""
    
    enhanced_doc = await llm_client.generate_documentation(
        content=doc_content,
        doc_type="confluence"
    )
    
    confluence_client = ConfluenceClient()
    
    page_id = confluence_client.create_page(
        space_key=space_key,
        title=f"Issue Analysis: {analysis.issue_id}",
        content=enhanced_doc or doc_content,
        parent_id=parent_page_id
    )
    
    if page_id:
        logger.info(f"Published documentation to Confluence page: {page_id}")
        confluence_client.add_labels(page_id, ["ai-analysis", "auto-generated"])
    
    return page_id

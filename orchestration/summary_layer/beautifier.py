"""
Response Beautifier

Cleans and crafts beautiful, well-structured messages for LLM consumption.
"""

import logging
import time
from typing import List, Dict, Any
from orchestration.github_llm.models import SourceResult, QueryType
from shared.llm_providers.factory import LLMFactory
from orchestration.summary_layer.response_cleaner import response_cleaner

logger = logging.getLogger(__name__)


class ResponseBeautifier:
    """Beautifies responses for LLM consumption"""
    
    def __init__(self, llm_provider: str = "auto"):
        """
        Initialize response beautifier with role-based provider selection
        
        Args:
            llm_provider: LLM provider to use ('auto', 'azure', 'together', 'openai')
        """
        from shared.llm_providers.resilient_orchestrator import get_resilient_orchestrator
        
        # Get provider based on role
        if llm_provider == "auto":
            orchestrator = get_resilient_orchestrator()
            llm_provider = orchestrator.get_provider_for_role("beautify")
        
        self.provider_name = llm_provider
        logger.info(f"✨ Response Beautifier initialized with provider: {llm_provider}")
    
    async def beautify(
        self,
        query: str,
        sources: List[SourceResult],
        summary: str,
        query_type: QueryType
    ) -> str:
        """
        Beautify response using LLM with enhanced logging
        
        Args:
            query: Original query
            sources: Source results
            summary: Generated summary
            query_type: Type of query
            
        Returns:
            Beautified, LLM-friendly response
        """
        logger.info("-" * 60)
        logger.info(f"✨ RESPONSE BEAUTIFIER START")
        logger.info(f"📝 Query: '{query[:80]}...'")
        logger.info(f"🎯 Query Type: {query_type.value}")
        logger.info(f"📊 Sources: {len(sources)}")
        logger.info(f"📄 Summary Length: {len(summary)} characters")
        logger.info("-" * 60)
        
        try:
            # Build context from sources
            context_start = time.time()
            context = self._build_context(sources, query_type)
            context_time = (time.time() - context_start) * 1000
            logger.info(f"🔗 Context built from {len(sources)} sources ({context_time:.2f}ms)")
            logger.info(f"   Context length: {len(context)} characters")
            
            # Create beautification prompt
            prompt_start = time.time()
            prompt = self._create_beautification_prompt(
                query=query,
                summary=summary,
                context=context,
                query_type=query_type
            )
            prompt_time = (time.time() - prompt_start) * 1000
            logger.info(f"📝 Beautification prompt created ({prompt_time:.2f}ms)")
            logger.info(f"   Prompt length: {len(prompt)} characters")
            
            # Use LLM to beautify
            llm_start = time.time()
            logger.info(f"🤖 Calling {self.provider_name.upper()} LLM for beautification...")
            
            # Use the resilient orchestrator for LLM calls
            from shared.llm_providers.resilient_orchestrator import get_resilient_orchestrator
            orchestrator = get_resilient_orchestrator()
            
            beautified, metadata = await orchestrator.chat_completion_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                preferred_provider=self.provider_name
            )
            llm_time = (time.time() - llm_start) * 1000
            
            logger.info(f"✅ LLM beautification completed ({llm_time:.2f}ms)")
            logger.info(f"   Response length: {len(beautified)} characters")
            logger.info(f"   Response preview: {beautified[:200]}...")
            
            # Clean the beautified response
            clean_start = time.time()
            logger.info("🧹 Cleaning beautified response...")
            cleaned, clean_metadata = response_cleaner.clean_with_metadata(beautified)
            clean_time = (time.time() - clean_start) * 1000
            logger.info(f"✅ Response cleaned ({clean_time:.2f}ms)")
            logger.info(f"   {clean_metadata}")
            
            logger.info("-" * 60)
            logger.info(f"✅ RESPONSE BEAUTIFIER COMPLETE")
            logger.info(f"⏱️  Total Time: {context_time + prompt_time + llm_time + clean_time:.2f}ms")
            logger.info("-" * 60)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"❌ Beautification failed: {e}", exc_info=True)
            logger.info("🔄 Using fallback formatting...")
            # Fallback to basic formatting
            fallback = self._fallback_formatting(query, summary, sources)
            logger.info(f"✅ Fallback formatting complete ({len(fallback)} characters)")
            # Clean the fallback response too
            fallback = response_cleaner.clean(fallback)
            logger.info(f"🧹 Fallback cleaned ({len(fallback)} characters)")
            logger.info("-" * 60)
            return fallback
    
    def _build_context(
        self,
        sources: List[SourceResult],
        query_type: QueryType
    ) -> str:
        """Build context from source results"""
        if not sources:
            return "No source context available."
        
        context_parts = []
        
        for idx, source in enumerate(sources, 1):
            repo = source.metadata.get('repo', 'Unknown')
            file_path = source.metadata.get('file_path', 'Unknown')
            
            context_parts.append(
                f"Source {idx} ({source.source_type}):\n"
                f"Repository: {repo}\n"
                f"File: {file_path}\n"
                f"Relevance: {source.relevance_score:.2f}\n"
                f"Content:\n{source.content[:500]}...\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _create_beautification_prompt(
        self,
        query: str,
        summary: str,
        context: str,
        query_type: QueryType
    ) -> str:
        """Create prompt for LLM beautification with rich formatting"""
        prompt = f"""You are a technical documentation expert. Your task is to create a visually stunning, 
modern response with rich formatting, icons, and clear structure.

User Query: {query}
Query Type: {query_type.value}

Raw Summary:
{summary}

Source Context:
{context}

CRITICAL FORMATTING REQUIREMENTS:
Create a beautifully formatted markdown response using these elements:

1. **START WITH AN ICON-RICH HEADER**:
   - Use emojis/icons (🎯 📊 🔍 💡 ⚡ 🚀 ✨ 📁 🔧 ⚠️ ✅ ❌ 📝 🎨)
   - Example: "## 🎯 API Implementations Found"

2. **USE COLORED CALLOUTS FOR KEY INFO**:
   - ✅ Success/Found items with checkmarks
   - ⚠️ Warnings or important notes
   - 💡 Key insights or tips
   - 📊 Statistics or metrics
   - 🔍 Search results
   - ❌ Missing items or errors

3. **STRUCTURED SECTIONS WITH ICONS**:
   - ### 📋 Overview
   - ### 🔑 Key Findings
   - ### 📂 File Locations
   - ### 💻 Code Examples
   - ### 📊 Summary
   - ### 🎯 Next Steps

4. **HIGHLIGHT IMPORTANT DETAILS**:
   - Use **bold** for important terms
   - Use `inline code` for file names, functions, variables
   - Use ```language blocks for code snippets
   - Use > blockquotes for important notes
   - Use bullet points with icons: 🔸 🔹 ▪️ • 

5. **FILE REFERENCES**:
   Format as: 📁 `path/to/file.ext` (line X-Y)

6. **METRICS AND STATS**:
   Format as:
   📊 **Statistics**:
   - ✅ Found: X items
   - 🎯 Relevance: XX%
   - ⏱️ Response time: Xms

7. **CODE BLOCKS**:
   Always use proper language tags:
   ```python
   def example():
       pass
   ```

8. **CLEAR VISUAL HIERARCHY**:
   - Use headers (##, ###) with icons
   - Add horizontal separators (---) between major sections
   - Group related items with consistent formatting

9. **END WITH ACTIONABLE SUMMARY**:
   ### 🎯 Summary
   Brief, icon-enhanced bullet points

REMEMBER: Make it visually engaging, modern, and easy to scan. Use icons liberally but tastefully.

Now create your beautifully formatted response:"""
        
        return prompt
    
    def _fallback_formatting(
        self,
        query: str,
        summary: str,
        sources: List[SourceResult]
    ) -> str:
        """Fallback formatting when LLM is unavailable - uses rich formatting"""
        
        # Build header
        formatted = f"""## 🔍 Search Results

### 📋 Query
> {query}

---

### 📊 Summary
{summary}

"""
        
        # Add results if available
        if sources:
            formatted += f"""---

### 🎯 Found {len(sources[:3])} Result{'s' if len(sources[:3]) != 1 else ''}

"""
            
            for idx, source in enumerate(sources[:3], 1):
                repo = source.metadata.get('repo', 'Unknown')
                file_path = source.metadata.get('file_path', 'Unknown')
                relevance_pct = source.relevance_score * 100
                
                # Icon based on relevance
                relevance_icon = "🟢" if relevance_pct >= 80 else "🟡" if relevance_pct >= 60 else "🟠"
                
                formatted += f"""
#### {relevance_icon} Result {idx} - {relevance_pct:.0f}% Match

📁 **File**: `{file_path}`  
🏢 **Repository**: {repo}  
📊 **Relevance**: {source.relevance_score:.2f}  
🔗 **Source**: {source.source_type}

**Preview:**
```
{source.content[:300]}...
```

---
"""
        else:
            formatted += """---

### ⚠️ No Results Found

The search didn't return any matching results. Try:
- 🔸 Broadening your search terms
- 🔸 Checking repository names
- 🔸 Using different keywords

"""
        
        # Add footer
        formatted += """
### 💡 Tip
For better results, make sure the repository is indexed in the Vector DB.
"""
        
        return formatted

"""Documentation Generator Service - LLM-driven documentation from prompts"""
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from shared.clients.github_client import GitHubClient
from shared.llm_providers.factory import get_llm_client

logger = logging.getLogger(__name__)


class DocumentationRequest(BaseModel):
    """Documentation generation request from user prompt"""
    prompt: str
    repository: Optional[str] = None
    max_files: int = 10
    format: str = "markdown"
    commit_to_github: bool = False
    commit_path: str = "docs/AI_GENERATED_DOCS.md"
    commit_message: Optional[str] = None


class DocumentationResult(BaseModel):
    """Generated documentation result"""
    success: bool
    documentation: Optional[str] = None
    files_analyzed: List[str] = []
    repository: Optional[str] = None
    github_commit: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DocGeneratorService:
    """Service for generating documentation from natural language prompts"""
    
    def __init__(self):
        self.github_client = GitHubClient()
    
    async def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Use LLM to parse user prompt and extract intent"""
        llm_provider = get_llm_client()
        
        parse_prompt = f"""You are a documentation assistant. Parse this user request and extract:
1. Repository name (owner/repo format) - if mentioned
2. Files or directories to document - specific paths if mentioned
3. Documentation task type (overview, API docs, architecture, function docs, etc.)
4. Any specific focus areas or requirements

User request: "{prompt}"

Respond in JSON format:
{{
    "repository": "owner/repo or null",
    "files": ["list of file paths or patterns"],
    "task_type": "type of documentation",
    "focus_areas": ["specific areas to focus on"],
    "search_query": "code search query if files not specified"
}}
"""
        
        try:
            response = await llm_provider.chat_completion(
                messages=[{"role": "user", "content": parse_prompt}],
                temperature=0.3
            )
            
            if response is None:
                logger.error("LLM response is None, using fallback parsing")
                return {
                    "repository": None,
                    "files": [],
                    "task_type": "general",
                    "focus_areas": [],
                    "search_query": None
                }
            
            import json
            parsed = json.loads(response.strip().strip('```json').strip('```').strip())
            logger.info(f"Parsed prompt: {parsed}")
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse prompt: {e}")
            return {
                "repository": None,
                "files": [],
                "task_type": "general",
                "focus_areas": [],
                "search_query": prompt
            }
    
    async def discover_files(
        self,
        repo_name: str,
        parsed_intent: Dict[str, Any]
    ) -> List[str]:
        """Discover relevant files based on parsed intent"""
        files_to_analyze = []
        
        # If specific files mentioned, use them
        if parsed_intent.get("files"):
            files_to_analyze = parsed_intent["files"]
            logger.info(f"Using specified files: {files_to_analyze}")
            return files_to_analyze
        
        # If search query provided, search for files
        if parsed_intent.get("search_query"):
            search_results = await self.github_client.search_code(
                repo_name=repo_name,
                query=parsed_intent["search_query"],
                max_results=10
            )
            
            if search_results:
                files_to_analyze = [r["path"] for r in search_results]
                logger.info(f"Found files via search: {files_to_analyze}")
                return files_to_analyze
        
        # Default: Get repository tree and select relevant files
        tree = await self.github_client.get_repository_tree(repo_name)
        if tree:
            # Filter for common code files
            common_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.md']
            code_files = [
                item["path"] for item in tree
                if item["type"] == "blob" and 
                any(item["path"].endswith(ext) for ext in common_extensions)
            ][:20]  # Limit to first 20 files
            
            logger.info(f"Using tree-based file discovery: {len(code_files)} files")
            return code_files
        
        return []
    
    async def analyze_files(
        self,
        repo_name: str,
        file_paths: List[str],
        task_type: str,
        focus_areas: List[str]
    ) -> str:
        """Fetch files and generate documentation using LLM"""
        llm_provider = get_llm_client()
        
        # Fetch file contents
        file_contents = await self.github_client.get_multiple_files(
            repo_name=repo_name,
            file_paths=file_paths
        )
        
        if not file_contents:
            return "No files could be fetched from the repository."
        
        # Build context for LLM
        code_context = ""
        for path, content in file_contents.items():
            if content:
                code_context += f"\n### File: {path}\n```\n{content[:2000]}\n```\n"  # Limit each file to 2000 chars
        
        focus_text = f"\nFocus on: {', '.join(focus_areas)}" if focus_areas else ""
        
        doc_prompt = f"""Generate comprehensive documentation for this codebase.

Repository: {repo_name}
Task Type: {task_type}{focus_text}

Code Files:
{code_context}

Please provide:
1. Overview of the codebase
2. Key components and their purposes
3. API documentation (if applicable)
4. Usage examples
5. Architecture notes

Format the documentation in clear Markdown with proper headers, code blocks, and explanations.
"""
        
        try:
            documentation = await llm_provider.chat_completion(
                messages=[{"role": "user", "content": doc_prompt}],
                temperature=0.5,
                max_tokens=3000
            )
            logger.info(f"Generated documentation ({len(documentation)} chars)")
            return documentation
        except Exception as e:
            logger.error(f"Failed to generate documentation: {e}")
            return f"Error generating documentation: {str(e)}"
    
    async def generate(self, request: DocumentationRequest) -> DocumentationResult:
        """Main entry point for documentation generation"""
        try:
            # Step 1: Parse the prompt to understand intent
            parsed_intent = await self.parse_prompt(request.prompt)
            
            # Step 2: Determine repository
            repo_name = request.repository or parsed_intent.get("repository")
            if not repo_name:
                return DocumentationResult(
                    success=False,
                    error_message="No repository specified. Please include repository name (owner/repo) in your prompt."
                )
            
            logger.info(f"Generating docs for {repo_name} with task: {parsed_intent.get('task_type')}")
            
            # Step 3: Discover files to analyze
            files_to_analyze = await self.discover_files(repo_name, parsed_intent)
            
            if not files_to_analyze:
                return DocumentationResult(
                    success=False,
                    repository=repo_name,
                    error_message="No relevant files found in the repository."
                )
            
            # Limit files to analyze
            files_to_analyze = files_to_analyze[:request.max_files]
            
            # Step 4: Generate documentation
            documentation = await self.analyze_files(
                repo_name=repo_name,
                file_paths=files_to_analyze,
                task_type=parsed_intent.get("task_type", "general"),
                focus_areas=parsed_intent.get("focus_areas", [])
            )
            
            # Optionally commit to GitHub
            github_commit_result = None
            if request.commit_to_github and documentation:
                commit_msg = request.commit_message or f"docs: Add AI-generated documentation for {parsed_intent.get('task_type', 'general')}"
                github_commit_result = await self.github_client.commit_documentation(
                    repo_name=repo_name,
                    doc_content=documentation,
                    file_path=request.commit_path,
                    commit_message=commit_msg
                )
                if github_commit_result:
                    logger.info(f"Documentation committed to GitHub: {github_commit_result.get('commit_url')}")
            
            return DocumentationResult(
                success=True,
                documentation=documentation,
                files_analyzed=files_to_analyze,
                repository=repo_name,
                github_commit=github_commit_result,
                metadata={
                    "task_type": parsed_intent.get("task_type"),
                    "focus_areas": parsed_intent.get("focus_areas"),
                    "files_count": len(files_to_analyze)
                }
            )
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return DocumentationResult(
                success=False,
                error_message=str(e)
            )


async def generate_documentation(
    prompt: str,
    repository: Optional[str] = None,
    max_files: int = 10,
    format: str = "markdown",
    commit_to_github: bool = False,
    commit_path: str = "docs/AI_GENERATED_DOCS.md",
    commit_message: Optional[str] = None
) -> DocumentationResult:
    """
    Generate documentation from natural language prompt
    
    Args:
        prompt: Natural language description of what to document
        repository: Optional repository override (owner/repo)
        max_files: Maximum number of files to analyze
        format: Output format (markdown, html, etc.)
        commit_to_github: Whether to commit generated docs to GitHub
        commit_path: Path where to save docs in repo
        commit_message: Custom commit message
    
    Returns:
        DocumentationResult with generated documentation
    """
    service = DocGeneratorService()
    
    request = DocumentationRequest(
        prompt=prompt,
        repository=repository,
        max_files=max_files,
        format=format,
        commit_to_github=commit_to_github,
        commit_path=commit_path,
        commit_message=commit_message
    )
    
    result = await service.generate(request)
    return result

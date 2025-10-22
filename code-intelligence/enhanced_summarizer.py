"""
Enhanced Code Summarizer with Technical and Business Context

Provides rich, structured summaries including:
- Technical implementation details
- Business logic and features
- Configuration and environment variables
- Exception handling and error cases
- API specifications and contracts
- Infrastructure configs (Docker, Helm, K8s)
"""

import asyncio
import re
from typing import Optional, Dict, List, Any
from pathlib import Path
import logging

from parsers.base_parser import CodeChunk
from repo_state import RepoState
from rate_limiter import RateLimitController, QuotaType
from summary_templates import EnhancedSummaryTemplate

logger = logging.getLogger(__name__)


class EnhancedCodeSummarizer:
    """
    Enhanced summarizer with rich technical and business context.
    
    Features:
    - Language-specific prompts (Java, Kotlin, Python, etc.)
    - File-type detection (Docker, Helm, API specs)
    - Structured summary extraction
    - Configuration and environment analysis
    - Exception and error handling insights
    """
    
    def __init__(
        self,
        repo_state: RepoState,
        rate_limiter: RateLimitController,
        azure_client=None
    ):
        self.repo_state = repo_state
        self.rate_limiter = rate_limiter
        self.azure_client = azure_client
        self.templates = EnhancedSummaryTemplate()
        
        if self.azure_client is None:
            self._init_azure_client()
    
    def _init_azure_client(self):
        """Initialize Azure OpenAI client"""
        try:
            from shared.azure_services.azure_ai_manager import azure_ai_manager
            if azure_ai_manager.models.is_available():
                self.azure_client = azure_ai_manager.models
                logger.info("✅ Using Azure OpenAI for enhanced summarization")
            else:
                logger.warning("Azure OpenAI not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
    
    def detect_file_type(self, file_path: str, content: str) -> str:
        """Detect special file types for targeted summarization"""
        file_path_lower = file_path.lower()
        
        # Kafka configurations
        if any(x in file_path_lower for x in ['kafka', 'producer', 'consumer', 'streams']):
            if any(x in content.lower() for x in ['kafka', 'topic', 'broker', 'partition']):
                return 'kafka'
        
        # Message queues
        if any(x in file_path_lower for x in ['rabbitmq', 'amqp', 'redis-stream', 'sqs', 'pubsub']):
            return 'message-queue'
        
        # Database schemas and migrations
        if any(x in file_path_lower for x in ['migration', 'schema', 'ddl', 'alembic', 'liquibase', 'flyway']):
            return 'database-schema'
        if file_path.endswith(('.sql', '.ddl')):
            if any(x in content.upper() for x in ['CREATE TABLE', 'ALTER TABLE', 'DROP TABLE', 'CREATE INDEX']):
                return 'database-schema'
        
        # Infrastructure as Code
        if file_path.endswith(('.tf', '.tfvars')) or 'terraform' in file_path_lower:
            return 'terraform'
        if 'cloudformation' in file_path_lower or file_path.endswith('.cfn.yaml'):
            return 'cloudformation'
        if 'ansible' in file_path_lower or file_path.endswith('.playbook.yml'):
            return 'ansible'
        
        # CI/CD Pipelines
        if '.github/workflows' in file_path:
            return 'github-actions'
        if '.gitlab-ci' in file_path_lower or file_path.endswith('.gitlab-ci.yml'):
            return 'gitlab-ci'
        if 'jenkinsfile' in file_path_lower:
            return 'jenkins'
        if '.circleci' in file_path:
            return 'circleci'
        if 'azure-pipelines' in file_path_lower:
            return 'azure-pipelines'
        
        # Monitoring/Observability
        if 'prometheus' in file_path_lower and file_path.endswith(('.yml', '.yaml')):
            return 'prometheus'
        if 'grafana' in file_path_lower:
            return 'grafana'
        if file_path.endswith('.alert.yml') or 'alerts' in file_path_lower:
            return 'alerting'
        
        # Service Mesh
        if any(x in file_path_lower for x in ['istio', 'linkerd', 'envoy']):
            return 'service-mesh'
        
        # API Gateway
        if any(x in file_path_lower for x in ['kong', 'nginx.conf', 'traefik', 'api-gateway']):
            return 'api-gateway'
        
        # Docker files
        if 'dockerfile' in file_path_lower or file_path.endswith('.dockerfile'):
            return 'docker'
        if 'docker-compose' in file_path_lower:
            return 'docker-compose'
        
        # Kubernetes/Helm
        if any(x in file_path_lower for x in ['helm', 'chart.yaml', 'values.yaml']):
            return 'helm'
        if 'k8s' in file_path_lower or 'kubernetes' in file_path_lower:
            return 'kubernetes'
        
        # API Specifications
        if 'openapi' in file_path_lower or 'swagger' in file_path_lower:
            return 'openapi'
        if file_path.endswith('.proto') or 'grpc' in file_path_lower:
            return 'protobuf'
        if file_path.endswith('.graphql') or 'schema.graphql' in file_path_lower:
            return 'graphql'
        
        # Config files
        if file_path.endswith(('.env', '.env.example', '.env.local')):
            return 'env'
        if file_path.endswith(('.yaml', '.yml')) and any(x in file_path_lower for x in ['config', 'application', 'settings']):
            return 'config-yaml'
        if file_path.endswith('.properties') or file_path.endswith('.conf'):
            return 'config'
        
        # Package/dependency files
        if file_path.endswith(('package.json', 'pom.xml', 'build.gradle', 'requirements.txt', 'Cargo.toml')):
            return 'dependencies'
        
        return 'code'
    
    def extract_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Extract rich metadata from code chunk"""
        content = chunk.content
        language = chunk.metadata.language
        
        metadata = {
            'imports': [],
            'exports': [],
            'classes': [],
            'functions': [],
            'exceptions': [],
            'annotations': [],
            'env_vars': [],
            'api_endpoints': [],
            'config_keys': []
        }
        
        # Extract imports/dependencies
        if language in ['python', 'java', 'kotlin', 'javascript', 'typescript']:
            metadata['imports'] = self._extract_imports(content, language)
        
        # Extract exceptions
        metadata['exceptions'] = self._extract_exceptions(content, language)
        
        # Extract annotations (Java/Kotlin)
        if language in ['java', 'kotlin']:
            metadata['annotations'] = self._extract_annotations(content)
        
        # Extract environment variables
        metadata['env_vars'] = self._extract_env_vars(content)
        
        # Extract API endpoints
        metadata['api_endpoints'] = self._extract_api_endpoints(content, language)
        
        # Extract config keys
        metadata['config_keys'] = self._extract_config_keys(content)
        
        return metadata
    
    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements"""
        imports = []
        
        patterns = {
            'python': r'(?:from\s+[\w.]+\s+)?import\s+[\w., ]+',
            'java': r'import\s+[\w.]+;',
            'kotlin': r'import\s+[\w.]+',
            'javascript': r'(?:import\s+.*?from\s+[\'"].*?[\'"]|require\([\'"].*?[\'"]\))',
            'typescript': r'import\s+.*?from\s+[\'"].*?[\'"]'
        }
        
        pattern = patterns.get(language)
        if pattern:
            imports = re.findall(pattern, content)
        
        return imports[:10]  # Limit to top 10
    
    def _extract_exceptions(self, content: str, language: str) -> List[str]:
        """Extract exception types"""
        exceptions = []
        
        # Common exception patterns
        patterns = [
            r'catch\s*\(\s*(\w+Exception)',  # Java/Kotlin/C#
            r'except\s+(\w+Error|\w+Exception)',  # Python
            r'throw\s+new\s+(\w+Exception)',  # Java/Kotlin
            r'raise\s+(\w+Error)',  # Python
        ]
        
        for pattern in patterns:
            exceptions.extend(re.findall(pattern, content))
        
        return list(set(exceptions))[:10]
    
    def _extract_annotations(self, content: str) -> List[str]:
        """Extract Java/Kotlin annotations"""
        return re.findall(r'@(\w+)(?:\(.*?\))?', content)[:15]
    
    def _extract_env_vars(self, content: str) -> List[str]:
        """Extract environment variable references"""
        patterns = [
            r'process\.env\.(\w+)',  # JavaScript/Node
            r'os\.getenv\([\'"](\w+)[\'"]\)',  # Python
            r'System\.getenv\([\'"](\w+)[\'"]\)',  # Java
            r'\$\{(\w+)\}',  # Shell/Docker/YAML
            r'env\.(\w+)',  # Generic
        ]
        
        env_vars = []
        for pattern in patterns:
            env_vars.extend(re.findall(pattern, content))
        
        return list(set(env_vars))[:10]
    
    def _extract_api_endpoints(self, content: str, language: str) -> List[str]:
        """Extract API endpoint definitions"""
        endpoints = []
        
        patterns = [
            r'@(?:Get|Post|Put|Delete|Patch)Mapping\([\'"](.+?)[\'"]\)',  # Spring
            r'@app\.(?:get|post|put|delete|patch)\([\'"](.+?)[\'"]\)',  # FastAPI/Flask
            r'router\.(?:get|post|put|delete|patch)\([\'"](.+?)[\'"]\)',  # Express
            r'@RequestMapping\([\'"](.+?)[\'"]\)',  # Spring
        ]
        
        for pattern in patterns:
            endpoints.extend(re.findall(pattern, content))
        
        return endpoints[:10]
    
    def _extract_config_keys(self, content: str) -> List[str]:
        """Extract configuration keys"""
        # Look for property access patterns
        patterns = [
            r'config\.get\([\'"](.+?)[\'"]\)',
            r'properties\.getProperty\([\'"](.+?)[\'"]\)',
            r'@Value\([\'"\$\{(.+?)\}[\'"]\)',  # Spring
        ]
        
        config_keys = []
        for pattern in patterns:
            config_keys.extend(re.findall(pattern, content))
        
        return list(set(config_keys))[:10]
    
    def build_enhanced_prompt(self, chunk: CodeChunk, metadata: Dict[str, Any]) -> str:
        """Build enhanced prompt with metadata"""
        file_type = self.detect_file_type(chunk.metadata.file_path, chunk.content)
        language = chunk.metadata.language
        
        # Select appropriate template based on file type
        if file_type in ['kafka', 'message-queue']:
            template = self.templates.KAFKA_TEMPLATE
        elif file_type == 'database-schema':
            template = self.templates.DATABASE_TEMPLATE
        elif file_type in ['terraform', 'cloudformation', 'ansible']:
            template = self.templates.IAC_TEMPLATE
        elif file_type in ['github-actions', 'gitlab-ci', 'jenkins', 'circleci', 'azure-pipelines']:
            template = self.templates.CICD_TEMPLATE
        elif file_type in ['prometheus', 'grafana', 'alerting']:
            template = self.templates.MONITORING_TEMPLATE
        elif file_type in ['docker', 'docker-compose', 'helm', 'kubernetes', 'service-mesh', 'api-gateway']:
            template = self.templates.INFRASTRUCTURE_TEMPLATE
        elif file_type in ['openapi', 'protobuf', 'graphql']:
            template = self.templates.API_SPEC_TEMPLATE
        elif file_type in ['env', 'config-yaml', 'config']:
            template = self.templates.CONFIG_TEMPLATE
        elif 'exception' in chunk.metadata.chunk_type.lower() or metadata['exceptions']:
            template = self.templates.EXCEPTION_TEMPLATE
        else:
            template = self.templates.CODE_TEMPLATE
        
        # Build symbol info
        symbol_info = ""
        if chunk.metadata.symbol_name:
            symbol_info = f"Symbol: {chunk.metadata.symbol_name}"
        
        # Add metadata context
        metadata_context = []
        if metadata['imports']:
            metadata_context.append(f"Imports: {', '.join(metadata['imports'][:5])}")
        if metadata['exceptions']:
            metadata_context.append(f"Exceptions: {', '.join(metadata['exceptions'])}")
        if metadata['annotations']:
            metadata_context.append(f"Annotations: {', '.join(metadata['annotations'][:5])}")
        if metadata['env_vars']:
            metadata_context.append(f"Env Vars: {', '.join(metadata['env_vars'][:5])}")
        if metadata['api_endpoints']:
            metadata_context.append(f"Endpoints: {', '.join(metadata['api_endpoints'][:3])}")
        
        if metadata_context:
            symbol_info += "\n" + "\n".join(metadata_context)
        
        # Format prompt
        prompt = template.format(
            language=language,
            file_path=chunk.metadata.file_path,
            chunk_type=chunk.metadata.chunk_type,
            file_type=file_type,
            symbol_info=symbol_info,
            content=chunk.content[:2000]  # Limit content length
        )
        
        return prompt
    
    async def summarize_chunk(
        self,
        chunk: CodeChunk,
        use_cache: bool = True
    ) -> str:
        """Generate enhanced summary with technical and business context"""
        
        # Check cache
        if use_cache:
            cached = self.repo_state.get_cached_summary(chunk.chunk_id)
            if cached:
                logger.debug(f"Cache hit for {chunk.chunk_id}")
                return cached
        
        # Extract metadata
        metadata = self.extract_metadata(chunk)
        
        # Generate enhanced summary
        try:
            summary = await self._generate_enhanced_summary(chunk, metadata)
            
            # Update cache
            self.repo_state.update_chunk_state(
                chunk_id=chunk.chunk_id,
                file_path=chunk.metadata.file_path,
                chunk_content=chunk.content,
                chunk_index=int(chunk.chunk_id.split('_')[-1]) if '_' in chunk.chunk_id else 0,
                summary=summary,
                status="summarized"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize {chunk.chunk_id}: {e}")
            return self._fallback_summary(chunk, metadata)
    
    async def _generate_enhanced_summary(
        self,
        chunk: CodeChunk,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate summary using Azure GPT-4o mini"""
        if not self.azure_client:
            logger.debug(f"No Azure client, using fallback for {chunk.chunk_id}")
            return self._fallback_summary(chunk, metadata)
        
        # Build enhanced prompt
        prompt = self.build_enhanced_prompt(chunk, metadata)
        
        # Log summarization details
        logger.debug(f"📝 Summarizing {chunk.chunk_id}")
        logger.debug(f"   File: {chunk.metadata.file_path}")
        logger.debug(f"   Type: {chunk.metadata.chunk_type}")
        logger.debug(f"   Symbol: {chunk.metadata.symbol_name or 'N/A'}")
        logger.debug(f"   Lines: {chunk.metadata.start_line}-{chunk.metadata.end_line}")
        logger.debug(f"   Prompt length: {len(prompt)} chars")
        logger.debug(f"   Metadata: imports={len(metadata.get('imports', []))}, "
                    f"exceptions={len(metadata.get('exceptions', []))}, "
                    f"annotations={len(metadata.get('annotations', []))}, "
                    f"env_vars={len(metadata.get('env_vars', []))}, "
                    f"endpoints={len(metadata.get('api_endpoints', []))}")
        
        # Call API with rate limiting
        async def call_api():
            logger.debug(f"   🔄 Calling Azure Chat Completion for {chunk.chunk_id}")
            response = await self.azure_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software architect analyzing code. Provide structured, technical summaries with business context, configurations, and error handling details."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4.1-mini",
                max_tokens=300,  # Increased for richer summaries
                temperature=0.2  # Lower for more factual
            )
            # Response is already a string, not a dict
            logger.debug(f"   ✅ Received summary for {chunk.chunk_id} ({len(response)} chars)")
            return response
        
        summary = await self.rate_limiter.submit(
            QuotaType.SUMMARIZATION,
            call_api,
            priority=3
        )
        
        return summary.strip() if summary else self._fallback_summary(chunk, metadata)
    
    def _fallback_summary(self, chunk: CodeChunk, metadata: Dict[str, Any]) -> str:
        """Generate rich fallback summary without AI"""
        meta = chunk.metadata
        parts = []
        
        # Basic info
        if meta.symbol_name:
            parts.append(f"**{meta.chunk_type}** `{meta.symbol_name}` in {Path(meta.file_path).name}")
        else:
            parts.append(f"**{meta.chunk_type}** in {Path(meta.file_path).name} (lines {meta.start_line}-{meta.end_line})")
        
        # Add metadata insights
        if metadata['imports']:
            parts.append(f"Dependencies: {', '.join(metadata['imports'][:3])}")
        
        if metadata['exceptions']:
            parts.append(f"Handles: {', '.join(metadata['exceptions'])}")
        
        if metadata['annotations']:
            parts.append(f"Annotations: {', '.join(metadata['annotations'][:3])}")
        
        if metadata['env_vars']:
            parts.append(f"Uses env: {', '.join(metadata['env_vars'][:3])}")
        
        if metadata['api_endpoints']:
            parts.append(f"Endpoints: {', '.join(metadata['api_endpoints'][:2])}")
        
        return " | ".join(parts)
    
    async def summarize_batch(
        self,
        chunks: List[CodeChunk],
        use_cache: bool = True
    ) -> Dict[str, str]:
        """Summarize chunks in smaller batches with real-time progress tracking"""
        total_chunks = len(chunks)
        logger.info(f"📝 Starting batch summarization of {total_chunks} chunks")
        logger.info(f"   Cache enabled: {use_cache}")
        
        # Check cache hits
        cache_hits = 0
        chunks_to_process = []
        cached_results = {}
        
        if use_cache:
            for chunk in chunks:
                cached_state = self.repo_state.get_chunk_state(chunk.chunk_id)
                if cached_state and cached_state.summary:
                    cache_hits += 1
                    cached_results[chunk.chunk_id] = cached_state.summary
                else:
                    chunks_to_process.append(chunk)
        else:
            chunks_to_process = chunks
        
        if cache_hits > 0:
            logger.info(f"   💾 Cache: {cache_hits}/{total_chunks} chunks already summarized")
            logger.info(f"   🔄 Will generate {len(chunks_to_process)} new summaries")
        
        # Process in smaller batches for better progress visibility
        batch_size = 10  # Process 10 at a time for progress updates
        result = cached_results.copy()
        error_count = 0
        fallback_count = 0
        total_processed = cache_hits
        
        logger.info(f"   ⏳ Processing {len(chunks_to_process)} summaries in batches of {batch_size}...")
        logger.info(f"   📊 Starting: {total_processed}/{total_chunks} complete ({(total_processed/total_chunks)*100:.1f}%)")
        
        for i in range(0, len(chunks_to_process), batch_size):
            batch = chunks_to_process[i:i + batch_size]
            batch_start_time = asyncio.get_event_loop().time()
            
            # Process this batch in parallel
            tasks = [self.summarize_chunk(chunk, use_cache) for chunk in batch]
            summaries = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for chunk, summary in zip(batch, summaries):
                if isinstance(summary, Exception):
                    error_count += 1
                    logger.debug(f"   ✗ Failed to summarize {chunk.chunk_id}: {summary}")
                    metadata = self.extract_metadata(chunk)
                    result[chunk.chunk_id] = self._fallback_summary(chunk, metadata)
                    fallback_count += 1
                else:
                    result[chunk.chunk_id] = summary
                
                total_processed += 1
            
            # Calculate progress and ETA
            progress_pct = (total_processed / total_chunks) * 100
            batch_time = asyncio.get_event_loop().time() - batch_start_time
            avg_time_per_chunk = batch_time / len(batch)
            remaining_chunks = total_chunks - total_processed
            eta_seconds = remaining_chunks * avg_time_per_chunk
            eta_minutes = eta_seconds / 60
            
            # Log progress with ETA
            logger.info(
                f"   📊 Progress: {total_processed}/{total_chunks} summaries "
                f"({progress_pct:.1f}% complete) - "
                f"ETA: {eta_minutes:.1f} min"
            )
        
        logger.info(f"   ✅ Batch complete: {len(result)} summaries generated (100.0%)")
        if error_count > 0:
            logger.warning(f"   ⚠️  {error_count} errors, {fallback_count} fallback summaries used")
        
        return result

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

logger = logging.getLogger(__name__)


class EnhancedSummaryTemplate:
    """Templates for different file types and languages"""
    
    # Python/Java/Kotlin code
    CODE_TEMPLATE = """Analyze this {language} code and provide a comprehensive summary:

File: {file_path}
Type: {chunk_type}
{symbol_info}

Code:
```{language}
{content}
```

Provide a structured summary with:
1. **Purpose**: What this code does (1-2 sentences)
2. **Technical Details**: Key algorithms, data structures, design patterns
3. **Business Logic**: What business problem it solves
4. **Dependencies**: External libraries, services, or modules used
5. **Configuration**: Environment variables, config files, or settings
6. **Error Handling**: Exception types, error cases handled
7. **API/Interface**: Public methods, endpoints, or contracts
8. **Performance Notes**: Any optimization, caching, or scalability concerns

Summary:"""

    # Configuration files (YAML, JSON, ENV)
    CONFIG_TEMPLATE = """Analyze this configuration file:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What this configuration controls
2. **Key Settings**: Most important configuration values
3. **Environment**: Development/staging/production settings
4. **Dependencies**: Services, databases, or external systems configured
5. **Security**: Secrets, API keys, or sensitive data (note presence, not values)
6. **Defaults**: Default values and recommended settings

Summary:"""

    # Docker/Kubernetes/Helm
    INFRASTRUCTURE_TEMPLATE = """Analyze this infrastructure configuration:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What infrastructure this defines
2. **Services**: Containers, pods, or services configured
3. **Networking**: Ports, load balancers, or ingress rules
4. **Storage**: Volumes, persistent storage, or databases
5. **Environment**: Environment variables and secrets
6. **Resources**: CPU, memory, or scaling settings
7. **Dependencies**: Service dependencies or init containers

Summary:"""

    # Kafka/Message Queue Configuration
    KAFKA_TEMPLATE = """Analyze this Kafka/messaging configuration:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What this messaging configuration does
2. **Topics/Queues**: Kafka topics, RabbitMQ queues, or message channels
3. **Producers**: Services that publish messages
4. **Consumers**: Services that consume messages
5. **Message Schema**: Data format and structure
6. **Partitioning**: Partition strategy and key
7. **Replication**: Replication factor and fault tolerance
8. **Performance**: Throughput, batching, compression settings
9. **Error Handling**: Dead letter queues, retry policies

Summary:"""

    # Database Schema/Migration
    DATABASE_TEMPLATE = """Analyze this database schema or migration:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What database changes this defines
2. **Tables/Collections**: Tables or collections modified
3. **Schema Changes**: Columns added/modified/removed
4. **Relationships**: Foreign keys, joins, references
5. **Indexes**: Indexes for query optimization
6. **Constraints**: Unique, not null, check constraints
7. **Migration Strategy**: Up/down migrations, rollback plan
8. **Data Impact**: Existing data handling

Summary:"""

    # Infrastructure as Code (Terraform, CloudFormation)
    IAC_TEMPLATE = """Analyze this infrastructure as code:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What infrastructure this provisions
2. **Resources**: Cloud resources created (EC2, S3, RDS, etc.)
3. **Networking**: VPCs, subnets, security groups
4. **Storage**: Volumes, buckets, databases
5. **Compute**: Instances, containers, serverless functions
6. **Variables**: Input variables and configuration
7. **Outputs**: Exported values for other modules
8. **Cost**: Estimated cost and resource sizing

Summary:"""

    # CI/CD Pipeline Configuration
    CICD_TEMPLATE = """Analyze this CI/CD pipeline configuration:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What this pipeline automates
2. **Triggers**: Events that start the pipeline (push, PR, schedule)
3. **Stages**: Build, test, deploy stages
4. **Jobs**: Specific jobs and their dependencies
5. **Environment**: Target environments (dev, staging, prod)
6. **Artifacts**: Build outputs and deployments
7. **Secrets**: Required credentials and API keys
8. **Notifications**: Alert and reporting mechanisms

Summary:"""

    # Monitoring/Observability Configuration
    MONITORING_TEMPLATE = """Analyze this monitoring/observability configuration:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What this monitoring configuration does
2. **Metrics**: Metrics collected and tracked
3. **Alerts**: Alert rules and thresholds
4. **Dashboards**: Visualization and graphs
5. **Targets**: Services or endpoints monitored
6. **Retention**: Data retention and storage
7. **Exporters**: Metric exporters and integrations
8. **SLOs/SLIs**: Service level objectives and indicators

Summary:"""

    # API Specifications (OpenAPI, GraphQL, Proto)
    API_SPEC_TEMPLATE = """Analyze this API specification:

File: {file_path}
Type: {file_type}

Content:
```
{content}
```

Provide a structured summary with:
1. **Purpose**: What this API provides
2. **Endpoints**: Key routes, methods, and operations
3. **Request/Response**: Data schemas and models
4. **Authentication**: Auth methods (OAuth, JWT, API keys)
5. **Error Codes**: HTTP status codes and error responses
6. **Rate Limiting**: Throttling or quota limits
7. **Versioning**: API version and compatibility

Summary:"""

    # Exception/Error handlers
    EXCEPTION_TEMPLATE = """Analyze this error handling code:

File: {file_path}
Type: {chunk_type}

Code:
```{language}
{content}
```

Provide a structured summary with:
1. **Purpose**: What errors this handles
2. **Exception Types**: Specific exceptions caught
3. **Recovery Strategy**: How errors are recovered or retried
4. **Logging**: Error logging and monitoring
5. **User Impact**: How errors affect end users
6. **Fallback**: Default values or graceful degradation

Summary:"""


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
            return self._fallback_summary(chunk, metadata)
        
        # Build enhanced prompt
        prompt = self.build_enhanced_prompt(chunk, metadata)
        
        # Call API with rate limiting
        async def call_api():
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
                model="gpt-4o-mini",
                max_tokens=300,  # Increased for richer summaries
                temperature=0.2  # Lower for more factual
            )
            return response.get("content", "")
        
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
        """Summarize multiple chunks in parallel"""
        tasks = [
            self.summarize_chunk(chunk, use_cache)
            for chunk in chunks
        ]
        
        summaries = await asyncio.gather(*tasks, return_exceptions=True)
        
        result = {}
        for chunk, summary in zip(chunks, summaries):
            if isinstance(summary, Exception):
                logger.error(f"Failed to summarize {chunk.chunk_id}: {summary}")
                metadata = self.extract_metadata(chunk)
                result[chunk.chunk_id] = self._fallback_summary(chunk, metadata)
            else:
                result[chunk.chunk_id] = summary
        
        return result

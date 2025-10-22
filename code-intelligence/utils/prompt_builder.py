"""
Prompt Builder - Builds enhanced prompts for summarization
"""
from typing import Dict, Any
import logging

from parsers.base_parser import CodeChunk
from utils.summary_templates import EnhancedSummaryTemplate

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds enhanced prompts with metadata for summarization"""
    
    def __init__(self):
        self.templates = EnhancedSummaryTemplate()
    
    def build_prompt(
        self,
        chunk: CodeChunk,
        metadata: Dict[str, Any],
        file_type: str
    ) -> str:
        """
        Build enhanced prompt with metadata.
        
        Args:
            chunk: Code chunk to summarize
            metadata: Extracted metadata
            file_type: Detected file type
            
        Returns:
            Formatted prompt string
        """
        language = chunk.metadata.language
        
        # Select appropriate template based on file type
        template = self._select_template(file_type, chunk, metadata)
        
        # Build symbol info
        symbol_info = self._build_symbol_info(chunk, metadata)
        
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
    
    def _select_template(
        self,
        file_type: str,
        chunk: CodeChunk,
        metadata: Dict[str, Any]
    ) -> str:
        """Select appropriate template based on file type"""
        if file_type in ['kafka', 'message-queue']:
            return self.templates.KAFKA_TEMPLATE
        elif file_type == 'database-schema':
            return self.templates.DATABASE_TEMPLATE
        elif file_type in ['terraform', 'cloudformation', 'ansible']:
            return self.templates.IAC_TEMPLATE
        elif file_type in ['github-actions', 'gitlab-ci', 'jenkins', 'circleci', 'azure-pipelines']:
            return self.templates.CICD_TEMPLATE
        elif file_type in ['prometheus', 'grafana', 'alerting']:
            return self.templates.MONITORING_TEMPLATE
        elif file_type in ['docker', 'docker-compose', 'helm', 'kubernetes', 'service-mesh', 'api-gateway']:
            return self.templates.INFRASTRUCTURE_TEMPLATE
        elif file_type in ['openapi', 'protobuf', 'graphql']:
            return self.templates.API_SPEC_TEMPLATE
        elif file_type in ['env', 'config-yaml', 'config']:
            return self.templates.CONFIG_TEMPLATE
        elif 'exception' in chunk.metadata.chunk_type.lower() or metadata['exceptions']:
            return self.templates.EXCEPTION_TEMPLATE
        else:
            return self.templates.CODE_TEMPLATE
    
    def _build_symbol_info(self, chunk: CodeChunk, metadata: Dict[str, Any]) -> str:
        """Build symbol info section with metadata"""
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
        
        return symbol_info

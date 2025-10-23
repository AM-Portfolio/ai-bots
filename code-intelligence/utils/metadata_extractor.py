"""
Metadata Extractor - Extracts metadata from code chunks
"""
import re
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts rich metadata from code chunks"""
    
    def extract_metadata(self, content: str, language: str) -> Dict[str, Any]:
        """
        Extract rich metadata from code content.
        
        Args:
            content: Code content
            language: Programming language
            
        Returns:
            Dictionary with extracted metadata
        """
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

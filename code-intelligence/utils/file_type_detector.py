"""
File Type Detector - Detects special file types for targeted summarization
"""
import logging

logger = logging.getLogger(__name__)


class FileTypeDetector:
    """Detects special file types for targeted summarization"""
    
    def detect_file_type(self, file_path: str, content: str) -> str:
        """
        Detect special file types for targeted summarization.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            File type string (e.g., 'kafka', 'docker', 'code')
        """
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

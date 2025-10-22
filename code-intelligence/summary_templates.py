"""
Summary Templates for Code Intelligence

Provides structured templates for different file types and code patterns.
Each template ensures comprehensive analysis covering technical, business,
and operational aspects.
"""


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

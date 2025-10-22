# 🚀 Comprehensive Tech Stack Support

The enhanced summarizer now supports **30+ technology stacks** with specialized analysis templates!

---

## 📊 Supported Technologies

### **1. Message Queues & Event Streaming** ⭐ NEW

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **Apache Kafka** | `kafka*.yml`, `kafka` in filename/content | Topics, partitions, replication, producers, consumers, DLQ, compression, batching |
| **RabbitMQ** | `rabbitmq*.yml`, `amqp` in filename | Queues, exchanges, bindings, routing keys, dead letter exchanges |
| **Redis Streams** | `redis-stream*.yml` | Stream names, consumer groups, message IDs |
| **AWS SQS** | `sqs*.yml` or `sqs` in content | Queue names, visibility timeout, DLQ, batch sizes |
| **Google Pub/Sub** | `pubsub*.yml` | Topics, subscriptions, acknowledgment deadlines |

**Example Summary:**
```
Purpose: Kafka producer configuration for user and order events
Topics:
  - user-events: 12 partitions, replication: 3, retention: 7 days
  - order-events: 24 partitions, replication: 3, retention: 30 days
Producers: acks=all, retries=3, compression=snappy, batch-size=16KB
Consumers: group=order-processor, auto-commit=false (exactly-once)
Partitioning: User ID as partition key for ordering
Replication: 3 replicas for fault tolerance
Performance: Batching enabled (10ms linger), snappy compression
Error Handling: DLQ enabled, max-retries=3
```

---

### **2. Database Schemas & Migrations** ⭐ NEW

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **SQL DDL** | `.sql`, `.ddl` files with `CREATE TABLE` | Tables, columns, relationships, indexes, constraints |
| **Alembic** (Python) | `alembic/versions/*.py` | Migration version, up/down functions, table changes |
| **Liquibase** (Java) | `liquibase/changelog*.xml` | Changesets, rollback procedures |
| **Flyway** (Java) | `flyway/V*.sql` | Version numbers, migration SQL |
| **Drizzle** (JS/TS) | `drizzle/*.ts` | Schema definitions, relations |

**Example Summary:**
```
Purpose: Initial e-commerce database schema with users and orders
Tables Created:
  - users: id (serial PK), email (unique), password_hash, status
  - orders: id (serial PK), user_id (FK), order_number, total_amount
  - order_items: id (serial PK), order_id (FK), quantity, unit_price
Relationships:
  - orders.user_id → users.id (CASCADE delete)
  - order_items.order_id → orders.id (CASCADE delete)
Indexes:
  - users: email, status, created_at (DESC)
  - orders: user_id, status, order_number, created_at (DESC)
Constraints:
  - CHECK: status IN ('active', 'suspended', 'deleted')
  - CHECK: total_amount >= 0, quantity > 0
Migration Strategy: Up migration with triggers, rollback via DROP TABLE
Data Impact: Creates new tables, no data migration needed
```

---

### **3. Infrastructure as Code (IaC)** ⭐ NEW

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **Terraform** | `.tf`, `.tfvars` files | Resources, VPC, subnets, databases, variables, outputs |
| **CloudFormation** | `.cfn.yaml`, `cloudformation` in filename | Stacks, resources, parameters, outputs |
| **Ansible** | `*.playbook.yml`, `ansible/` directory | Playbooks, tasks, roles, variables, handlers |
| **Pulumi** | `Pulumi*.yaml` | Resources, stack configs |

**Example Summary:**
```
Purpose: AWS infrastructure for production e-commerce application
Resources Created:
  - VPC: 10.0.0.0/16 with DNS support
  - Subnets: 2 public (10.0.0-1.0/24), 2 private (10.0.10-11.0/24)
  - RDS PostgreSQL: db.t3.medium, 100GB gp3, encryption enabled
  - ElastiCache Redis: cache.t3.medium, Redis 7.0
  - Security Groups: RDS (port 5432), Redis (port 6379)
Networking:
  - 2 availability zones for high availability
  - Public subnets with internet gateway
  - Private subnets for database tier
Storage:
  - RDS: 100GB encrypted gp3 with 7-day backups
  - Final snapshot on deletion
Compute: N/A (database-only infrastructure)
Variables:
  - aws_region (default: us-east-1)
  - environment (default: production)
  - db_username, db_password (sensitive)
Outputs:
  - vpc_id, database_endpoint, redis_endpoint
Cost: Estimated $200-300/month (db.t3.medium + cache.t3.medium + storage)
```

---

### **4. CI/CD Pipelines** ⭐ NEW

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **GitHub Actions** | `.github/workflows/*.yml` | Triggers, jobs, steps, environments, secrets |
| **GitLab CI/CD** | `.gitlab-ci.yml` | Stages, jobs, rules, artifacts |
| **Jenkins** | `Jenkinsfile` | Stages, steps, parameters, credentials |
| **CircleCI** | `.circleci/config.yml` | Workflows, jobs, executors |
| **Azure Pipelines** | `azure-pipelines.yml` | Triggers, stages, jobs, deployment |

**Example Summary:**
```
Purpose: Automated build, test, and deployment pipeline
Triggers:
  - push to main branch
  - pull_request to main
  - schedule: daily at 2 AM UTC
Stages:
  1. Build: Compile code, run linters
  2. Test: Unit tests, integration tests, coverage
  3. Deploy: Deploy to staging, then production
Jobs:
  - build: Node.js 18, npm install, npm run build
  - test: Run Jest tests, upload coverage to Codecov
  - deploy-staging: Deploy to staging environment (auto)
  - deploy-production: Deploy to production (manual approval)
Environment: Uses staging and production environments
Artifacts: Built assets uploaded to S3
Secrets: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DOCKER_PASSWORD
Notifications: Slack notification on failure
```

---

### **5. Monitoring & Observability** ⭐ NEW

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **Prometheus** | `prometheus*.yml` | Scrape configs, targets, alert rules |
| **Grafana** | `grafana/*.json` | Dashboards, panels, queries, data sources |
| **Alert Rules** | `*.alert.yml`, `alerts/` directory | Alert conditions, thresholds, severity |
| **Datadog** | `datadog*.yml` | Monitors, metrics, log pipelines |
| **New Relic** | `newrelic.yml` | APM config, transaction traces |

**Example Summary:**
```
Purpose: Prometheus monitoring for microservices
Metrics Collected:
  - HTTP request duration (p50, p95, p99)
  - Database query latency
  - Cache hit/miss rates
  - CPU and memory usage
Alerts Configured:
  - HighErrorRate: >5% errors for 5 minutes → severity: critical
  - SlowRequests: p99 latency >2s for 10 minutes → severity: warning
  - DatabaseDown: DB unreachable for 1 minute → severity: critical
Dashboards: Service health, request rates, error rates
Targets:
  - api-service:8080/metrics (scrape: 15s)
  - db-exporter:9187/metrics (scrape: 30s)
Retention: 15 days local storage
Exporters: node_exporter, postgres_exporter, redis_exporter
SLOs: 99.9% uptime, p99 latency <500ms
```

---

### **6. Service Mesh & API Gateways** ⭐ NEW

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **Istio** | `istio/*.yaml` | Virtual services, destination rules, gateways |
| **Linkerd** | `linkerd*.yaml` | Service profiles, traffic splits |
| **Kong** | `kong.yml`, `kong.conf` | Routes, services, plugins, upstreams |
| **Nginx** | `nginx.conf` | Server blocks, locations, upstreams, SSL |
| **Traefik** | `traefik*.yml` | Routers, services, middlewares |

---

### **7. Container Orchestration**

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **Docker** | `Dockerfile`, `*.dockerfile` | Base image, layers, ports, env vars, volumes |
| **Docker Compose** | `docker-compose*.yml` | Services, networks, volumes, dependencies |
| **Kubernetes** | `k8s/*.yaml`, `*-deployment.yaml` | Deployments, services, ingress, config maps |
| **Helm** | `Chart.yaml`, `values.yaml` | Chart metadata, templates, values |

---

### **8. API Specifications**

| Technology | Detection | What Gets Extracted |
|------------|-----------|---------------------|
| **OpenAPI/Swagger** | `openapi.yaml`, `swagger.json` | Paths, methods, schemas, responses |
| **GraphQL** | `schema.graphql`, `*.graphql` | Types, queries, mutations, subscriptions |
| **gRPC/Protobuf** | `*.proto` | Services, messages, RPCs |

---

### **9. Programming Languages**

| Language | Tree-Sitter | What Gets Extracted |
|----------|-------------|---------------------|
| **Python** | ✅ Yes | Functions, classes, decorators, async/await |
| **JavaScript/TypeScript** | ✅ Yes | Functions, classes, arrow functions, exports |
| **Java** | 🔄 Fallback | Classes, methods, annotations (@RestController, etc.) |
| **Kotlin** | 🔄 Fallback | Classes, functions, coroutines, data classes |
| **C/C++** | 🔄 Fallback | Functions, classes, templates |
| **Dart** (Flutter) | 🔄 Fallback | Widgets, classes, async functions |
| **Go** | 🔄 Fallback | Functions, structs, interfaces |
| **Rust** | 🔄 Fallback | Functions, structs, traits, async |

---

## 🎯 How It Works

### **Automatic Detection**
The summarizer analyzes both **filename** and **content** to determine the file type:

```python
# Examples of automatic detection:
kafka-config.yml + "kafka: bootstrap-servers" → KAFKA template
migration_001.sql + "CREATE TABLE" → DATABASE template
main.tf + "resource \"aws_vpc\"" → TERRAFORM template
.github/workflows/ci.yml → CI/CD template
prometheus.yml → MONITORING template
```

### **Specialized Templates**
Each technology gets a **custom prompt template** that extracts relevant information:

| Template | Focus Areas |
|----------|-------------|
| **KAFKA_TEMPLATE** | Topics, partitions, replication, producers, consumers, DLQ |
| **DATABASE_TEMPLATE** | Tables, indexes, constraints, foreign keys, migrations |
| **IAC_TEMPLATE** | Resources, networking, storage, variables, costs |
| **CICD_TEMPLATE** | Triggers, stages, jobs, environments, secrets |
| **MONITORING_TEMPLATE** | Metrics, alerts, dashboards, SLOs |
| **CODE_TEMPLATE** | Purpose, technical details, business logic, APIs |

---

## 📊 Coverage Summary

| Category | Technologies Supported | File Types |
|----------|----------------------|------------|
| **Message Queues** | Kafka, RabbitMQ, Redis, SQS, Pub/Sub | 5+ |
| **Databases** | PostgreSQL, MySQL, MongoDB, migrations | 10+ |
| **IaC** | Terraform, CloudFormation, Ansible | 4+ |
| **CI/CD** | GitHub Actions, GitLab, Jenkins, CircleCI | 5+ |
| **Monitoring** | Prometheus, Grafana, Datadog, New Relic | 5+ |
| **Containers** | Docker, K8s, Helm, Compose | 4+ |
| **APIs** | OpenAPI, GraphQL, gRPC/Protobuf | 3+ |
| **Languages** | Python, Java, Kotlin, JS/TS, C++, Dart, Go, Rust | 10+ |

**Total: 50+ specific technology stacks with intelligent detection and analysis!**

---

## 🚀 Usage

### No Configuration Required!
Just run the pipeline - technology detection is automatic:

```bash
python code-intelligence/embed_repo.py
```

### Examples with New Tech Stacks

**Kafka Configuration:**
```bash
# Embed Kafka configs
python embed_repo.py --repo ./kafka-project

# Query: "What's our Kafka replication strategy?"
# Finds: kafka-config.yml with detailed replication settings
```

**Database Migrations:**
```bash
# Embed database migrations
python embed_repo.py --repo ./backend/migrations

# Query: "What indexes do we have on the users table?"
# Finds: migration files with index definitions
```

**Terraform Infrastructure:**
```bash
# Embed Terraform configs
python embed_repo.py --repo ./infrastructure

# Query: "What AWS resources are we using?"
# Finds: All .tf files with resource definitions
```

**CI/CD Pipelines:**
```bash
# Embed GitHub Actions
python embed_repo.py --repo ./.github/workflows

# Query: "What secrets does our deployment need?"
# Finds: Workflow files with secret requirements
```

---

## 🎉 What This Enables

### **1. Cross-Stack Search**
Query across all your infrastructure:
```
Query: "What services use the production database?"
Results:
  - app.py (connects via DATABASE_URL)
  - docker-compose.yml (defines db service)
  - main.tf (provisions RDS instance)
  - migration_001.sql (creates schema)
  - .github/workflows/deploy.yml (runs migrations)
```

### **2. Dependency Discovery**
Find what depends on what:
```
Query: "What uses Redis for caching?"
Results:
  - UserService.py (caching layer)
  - docker-compose.yml (redis service)
  - terraform/cache.tf (ElastiCache provisioning)
  - app-config.yml (REDIS_URL configuration)
```

### **3. Configuration Tracking**
Track env vars across the stack:
```
Query: "Where is API_KEY used?"
Results:
  - .env.example (API_KEY=your-key-here)
  - docker-compose.yml (API_KEY=${API_KEY})
  - main.tf (API_KEY as variable)
  - api-client.py (os.getenv('API_KEY'))
```

### **4. Error Handling Audit**
Find all error handling:
```
Query: "How do we handle database connection failures?"
Results:
  - UserService.py (ConnectionError → HTTP 503)
  - docker-compose.yml (restart: unless-stopped)
  - main.tf (backup_retention_period: 7)
  - prometheus.yml (alert: DatabaseDown)
```

---

## 📚 Next Steps

1. **Test on your tech stack**:
   ```bash
   python embed_repo.py --repo your-project --max-files 20
   ```

2. **Check the summaries** - They now include tech-specific details

3. **Query across technologies** - Find connections between services, configs, and infrastructure

Your code intelligence system now understands **every layer of your tech stack**! 🚀

# Comprehensive Database Architecture & Schema Design

This directory contains the complete database architecture design for integrating Graph-Sitter code analysis, Codegen SDK task management, and Contexten event orchestration systems.

## 📁 Directory Structure

```
research/database-architecture/
├── docs/
│   └── comprehensive-database-architecture.md  # Complete architecture documentation
├── schemas/
│   ├── tasks_schema.sql                        # Task management and execution tracking
│   ├── codebases_schema.sql                    # Repository and code analysis data
│   ├── events_schema.sql                       # Multi-platform event tracking (ClickHouse)
│   ├── projects_schema.sql                     # Project and workflow management
│   ├── evaluations_schema.sql                  # Effectiveness and outcome analysis
│   ├── analytics_schema.sql                    # Performance metrics and analytics
│   ├── relationships_schema.sql                # Inter-entity relationship mapping
│   ├── cache_schema.sql                        # Query optimization and result caching
│   ├── audit_schema.sql                        # Change tracking and audit trails
│   └── indexes_schema.sql                      # Advanced indexing strategies
├── migrations/
│   └── 001_initial_setup.sql                   # Initial database setup migration
├── interfaces/
│   └── database_interface.py                   # Database abstraction layer
└── README.md                                   # This file
```

## 🏗️ Architecture Overview

### Hybrid Database Strategy

The architecture employs a hybrid approach combining:

- **PostgreSQL (OLTP)**: Transactional data, complex relationships, real-time operations
- **ClickHouse (OLAP)**: High-volume event ingestion, time-series analytics, reporting

### Core Components

1. **Tasks Management** (`tasks_schema.sql`)
   - Task creation, assignment, and tracking
   - Task dependencies and workflows
   - Task execution history and automation
   - Performance metrics and analytics

2. **Codebase Analysis** (`codebases_schema.sql`)
   - Repository metadata and configuration
   - File structure and content analysis
   - Code relationships and dependencies
   - Quality metrics and hotspot detection

3. **Event Processing** (`events_schema.sql`)
   - Multi-platform event ingestion (Linear, Slack, GitHub, deployments)
   - Real-time event processing and correlation
   - Event-driven workflow triggers
   - Cross-system event analytics

4. **Project Management** (`projects_schema.sql`)
   - Project lifecycle and metadata management
   - Team collaboration and resource allocation
   - Workflow definition and execution
   - Project analytics and reporting

5. **Evaluation System** (`evaluations_schema.sql`)
   - Performance evaluation frameworks
   - Effectiveness tracking and analysis
   - AI agent performance evaluation
   - Outcome measurement and benchmarking

6. **Analytics Engine** (`analytics_schema.sql`)
   - Real-time and historical analytics
   - Dashboard and reporting infrastructure
   - Trend analysis and predictions
   - Performance monitoring

7. **Relationship Mapping** (`relationships_schema.sql`)
   - Cross-system entity relationships
   - Dependency mapping and analysis
   - Relationship strength and confidence scoring
   - Graph-based analytics

8. **Caching Layer** (`cache_schema.sql`)
   - Query result caching
   - Performance optimization
   - Cache statistics and monitoring

9. **Audit System** (`audit_schema.sql`)
   - Comprehensive change tracking
   - Compliance and security logging
   - Data retention policies

10. **Advanced Indexing** (`indexes_schema.sql`)
    - Performance-optimized indexes
    - Full-text search capabilities
    - JSON and array indexing strategies

## 🚀 Quick Start

### 1. Database Setup

```bash
# PostgreSQL setup
createdb comprehensive_db
psql comprehensive_db -f migrations/001_initial_setup.sql

# Apply core schemas
psql comprehensive_db -f schemas/tasks_schema.sql
psql comprehensive_db -f schemas/projects_schema.sql
psql comprehensive_db -f schemas/codebases_schema.sql
# ... continue with other schemas

# ClickHouse setup (for events)
clickhouse-client --query "CREATE DATABASE events_db"
clickhouse-client --database events_db < schemas/events_schema.sql
```

### 2. Python Interface Usage

```python
from interfaces.database_interface import create_database_interface, DatabaseConfig

# Configure database connections
config = DatabaseConfig(
    postgresql_url="postgresql://user:pass@localhost/comprehensive_db",
    clickhouse_url="http://localhost:8123/events_db",
    enable_caching=True
)

# Create database interface
db = create_database_interface(config, implementation="hybrid")

# Connect to databases
await db.connect()

# Example: Create a task
task_data = {
    "title": "Implement new feature",
    "description": "Add user authentication",
    "project_id": 1,
    "assignee_id": 2,
    "priority": 80
}
task = await db.create_task(task_data)

# Example: Ingest an event
event_data = {
    "event_type": "task_created",
    "source_platform": "linear",
    "organization_id": 1,
    "task_id": task["id"],
    "event_data": {"action": "created", "user_id": 2}
}
await db.ingest_event(event_data)

# Example: Get analytics
metrics = await db.get_real_time_metrics(
    organization_id=1,
    metric_names=["active_tasks", "completion_rate"]
)
```

## 📊 Key Features

### Scalability
- Horizontal scaling with organization-based sharding
- Time-based partitioning for event data
- Read replicas for analytical workloads
- Automatic data archiving and retention

### Performance
- Advanced indexing strategies (B-tree, GIN, GiST)
- Query result caching with Redis
- Materialized views for common aggregations
- Connection pooling and query optimization

### Flexibility
- JSON/JSONB fields for extensible metadata
- EAV patterns for dynamic attributes
- Configurable evaluation frameworks
- Plugin-friendly architecture

### Security
- Role-based access control (RBAC)
- Comprehensive audit logging
- Data encryption at rest and in transit
- Compliance tracking (GDPR, HIPAA, SOX)

### Analytics
- Real-time dashboards and KPIs
- Trend analysis and predictions
- Cross-system correlation analysis
- Custom report generation

## 🔧 Configuration

### Environment Variables

```bash
# PostgreSQL Configuration
DATABASE_URL=postgresql://user:pass@localhost/comprehensive_db
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT=30

# ClickHouse Configuration
CLICKHOUSE_URL=http://localhost:8123/events_db
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Application Configuration
ENABLE_CACHING=true
ENABLE_AUDIT_LOGGING=true
DATA_RETENTION_DAYS=365
```

### Database Tuning

```sql
-- PostgreSQL configuration recommendations
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

## 📈 Monitoring and Maintenance

### Health Checks

```python
# Check database health
health = await db.health_check()
print(f"PostgreSQL: {health['postgresql']['status']}")
print(f"ClickHouse: {health['clickhouse']['status']}")
print(f"Cache: {health['cache']['status']}")
```

### Performance Monitoring

```sql
-- Monitor query performance
SELECT * FROM query_performance 
WHERE execution_time_ms > 1000 
ORDER BY executed_at DESC;

-- Monitor cache hit rates
SELECT * FROM cache_statistics 
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC;
```

### Data Retention

```sql
-- Configure retention policies
INSERT INTO data_retention_policies (organization_id, table_name, retention_days) VALUES
(1, 'events', 365),
(1, 'audit_logs', 2555),  -- 7 years
(1, 'performance_metrics', 90);
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from interfaces.database_interface import create_database_interface

@pytest.fixture
async def db_interface():
    config = DatabaseConfig(
        postgresql_url="postgresql://test:test@localhost/test_db",
        clickhouse_url="http://localhost:8123/test_events"
    )
    db = create_database_interface(config)
    await db.connect()
    yield db
    await db.disconnect()

async def test_task_creation(db_interface):
    task_data = {"title": "Test Task", "organization_id": 1}
    task = await db_interface.create_task(task_data)
    assert task["id"] is not None
    assert task["title"] == "Test Task"
```

### Load Testing

```bash
# Use pgbench for PostgreSQL load testing
pgbench -i -s 10 comprehensive_db
pgbench -c 10 -j 2 -t 1000 comprehensive_db

# Use clickhouse-benchmark for ClickHouse
echo "SELECT count() FROM events WHERE timestamp >= now() - INTERVAL 1 DAY" | \
clickhouse-benchmark --iterations=1000 --concurrency=10
```

## 🔄 Migration Strategy

### Schema Versioning

All schema changes are tracked in the `schema_migrations` table:

```sql
SELECT version, description, applied_at FROM schema_migrations ORDER BY applied_at;
```

### Rolling Updates

1. **Backward Compatible Changes**: Apply directly to production
2. **Breaking Changes**: Use blue-green deployment strategy
3. **Data Migrations**: Run during maintenance windows with progress tracking

### Rollback Procedures

```sql
-- Rollback example
BEGIN;
-- Apply rollback SQL from migration
-- Verify data integrity
COMMIT; -- or ROLLBACK if issues found
```

## 📚 Additional Resources

- [Complete Architecture Documentation](docs/comprehensive-database-architecture.md)
- [API Documentation](interfaces/database_interface.py)
- [Performance Tuning Guide](docs/performance-tuning.md)
- [Security Best Practices](docs/security-guide.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## 🤝 Contributing

1. Review the architecture documentation
2. Follow the established schema patterns
3. Add appropriate indexes and constraints
4. Include comprehensive tests
5. Update documentation

## 📄 License

This database architecture is part of the Graph-Sitter + Codegen + Contexten integration system.

---

**⚠️ Important**: This database architecture is designed for production use and includes advanced features for scalability, performance, and security. Ensure proper testing and validation before deploying to production environments.


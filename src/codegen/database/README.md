# 🗄️ Codegen Database Architecture

## Overview

This package implements a comprehensive database architecture for Codegen, transforming it from a memory-based system to a fully persistent, event-driven platform with real-time UI synchronization.

## 🏗️ Architecture Components

### 1. Database Models (`models/`)

Complete SQLAlchemy models representing all Codegen entities:

- **Organizations**: `Organization`, `OrganizationSettings`, `OrganizationMember`
- **Users**: `User`, `UserSession`, `APIToken`
- **Agents**: `AgentRun`, `AgentRunLog`, `AgentRunState`, `AgentTask`
- **Repositories**: `Repository`, `RepositorySettings`, `GitBranch`, `GitCommit`
- **PRDs**: `PRDTemplate`, `PRDGeneration`, `PRDTask`, `PRDProgress`
- **Events**: `SystemEvent`, `EventSubscription`
- **Webhooks**: `WebhookEndpoint`, `WebhookEvent`, `WebhookDelivery`

### 2. Database Connection (`connection.py`)

- PostgreSQL connection management with pooling
- Health monitoring and connection validation
- Environment-based configuration
- Automatic reconnection and error handling

### 3. Database Middleware (`middleware.py`)

High-level database operations with:
- CRUD operations with event emission
- Query optimization and relationship loading
- Transaction management
- Soft delete and audit trail support

### 4. Event System (`events.py`)

Real-time event emission and delivery:
- **EventEmitter**: System-wide event handling
- **WebhookManager**: HTTP webhook delivery with retries
- **WebSocketManager**: Real-time UI updates

### 5. UI Data Service (`ui_data_service.py`)

Database-backed data for UI components:
- Replaces all static data sources in TUI
- Real-time subscription system
- Efficient database queries with filtering

## 🚀 Quick Start

### 1. Database Setup

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/codegen"
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20
```

### 2. Initialize Database

```python
from codegen.database import init_database

# Create all tables
init_database()
```

### 3. Use in Your Code

```python
from codegen.database import get_database_middleware, get_ui_data_service

# Database operations
middleware = get_database_middleware()
user = middleware.create(User, {
    'email': 'user@example.com',
    'full_name': 'John Doe'
})

# UI data service
ui_service = get_ui_data_service()
organizations = ui_service.get_user_organizations(user.id)
```

## 📊 Data Flow Migration

### Before: Static/Memory-Based Data

```python
# OLD: Direct API calls and memory storage
class OldTUI:
    def __init__(self):
        self.agent_runs = []  # Static list
        self.organizations = []  # Static list
    
    def load_data(self):
        # Direct API call
        response = requests.get(f"{API_ENDPOINT}/agent/runs")
        self.agent_runs = response.json()
    
    def refresh_data(self):
        # Manual refresh
        self.load_data()
```

### After: Database-Backed with Real-Time Updates

```python
# NEW: Database-backed with real-time updates
class NewTUI:
    def __init__(self):
        self.ui_service = get_ui_data_service()
    
    async def load_data(self):
        # Database query
        self.agent_runs, total = self.ui_service.get_agent_runs(org_id)
        
        # Subscribe to real-time updates
        self.ui_service.subscribe_to_updates(
            user_id=user_id,
            org_id=org_id,
            callback=self.handle_update
        )
    
    def handle_update(self, event):
        # Automatic real-time updates
        if event['event_type'] == 'agentrun.created':
            self.refresh_agent_runs()
```

## 🔄 Event-Driven Architecture

### Event Types

All database operations emit events:

```python
# Events emitted automatically
'organization.created'
'organization.updated'
'organization.deleted'

'user.created'
'user.updated'
'user.login'

'agentrun.created'
'agentrun.updated'
'agentrun.started'
'agentrun.completed'
'agentrun.failed'

'repository.created'
'repository.updated'
```

### Webhook Integration

```python
# Webhook endpoints receive events
{
    "event_id": "evt_123",
    "event_type": "agentrun.completed",
    "timestamp": "2024-01-01T12:00:00Z",
    "data": {
        "id": "run_456",
        "status": "completed",
        "organization_id": "org_789"
    },
    "organization_id": "org_789"
}
```

### WebSocket Real-Time Updates

```javascript
// Frontend receives real-time updates
websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'event') {
        handleRealtimeUpdate(data.event);
    }
};
```

## 🔧 Configuration

### Environment Variables

```bash
# Database Connection
DATABASE_URL=postgresql://user:pass@host:port/db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false

# Individual Components (alternative to DATABASE_URL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=codegen
DB_USER=codegen
DB_PASSWORD=codegen
```

### Connection Pooling

```python
# Automatic connection pooling
config = DatabaseConfig()
manager = DatabaseManager(config)

# Health check
health = manager.health_check()
print(health['status'])  # 'healthy' or 'unhealthy'
```

## 📈 Performance Features

### Query Optimization

```python
# Efficient relationship loading
runs = middleware.list_with_filters(
    AgentRun,
    filters={'organization_id': org_id},
    relationships=['created_by_user', 'repository'],
    limit=50,
    offset=0
)
```

### Connection Pooling

- Automatic connection validation (`pool_pre_ping=True`)
- Connection recycling every hour
- Overflow handling for traffic spikes
- Health monitoring and metrics

### Caching Integration

```python
# Built-in caching support (can be extended)
@cached(ttl=300)  # 5 minutes
def get_organization_stats(org_id: str):
    return ui_service.get_organization_stats(org_id)
```

## 🔒 Security Features

### Audit Trail

All models support audit tracking:

```python
class AuditMixin:
    created_by_id = Column(UUID)
    updated_by_id = Column(UUID)
    created_from_ip = Column(String)
    created_context = Column(JSON)
```

### Soft Delete

```python
# Soft delete support
user.soft_delete()  # Marks as deleted
user.restore()      # Restores deleted record
```

### Webhook Security

```python
# HMAC signature verification
signature = hmac.new(
    secret.encode('utf-8'),
    payload.encode('utf-8'),
    hashlib.sha256
).hexdigest()

headers['X-Codegen-Signature'] = f"sha256={signature}"
```

## 🧪 Testing

### Database Testing

```python
import pytest
from codegen.database import init_database, close_database

@pytest.fixture
def db_session():
    # Setup test database
    init_database(drop_existing=True)
    yield
    close_database()

def test_user_creation(db_session):
    middleware = get_database_middleware()
    user = middleware.create(User, {
        'email': 'test@example.com'
    })
    assert user.email == 'test@example.com'
```

### Event Testing

```python
def test_event_emission():
    emitter = get_event_emitter()
    events = []
    
    def handler(event):
        events.append(event)
    
    emitter.on('test.event', handler)
    emitter.emit('test.event', {'data': 'test'})
    
    assert len(events) == 1
    assert events[0].event_type == 'test.event'
```

## 📚 Migration Guide

### Step 1: Replace Static Data Sources

```python
# BEFORE
class TUI:
    def __init__(self):
        self.agent_runs = []  # Static list
    
    def load_runs(self):
        response = requests.get(API_URL)
        self.agent_runs = response.json()

# AFTER
class TUI:
    def __init__(self):
        self.ui_service = get_ui_data_service()
    
    async def load_runs(self):
        runs, total = self.ui_service.get_agent_runs(org_id)
        self.agent_runs = runs
```

### Step 2: Add Real-Time Updates

```python
# Subscribe to database changes
self.ui_service.subscribe_to_updates(
    user_id=user_id,
    org_id=org_id,
    callback=self.handle_realtime_update
)

def handle_realtime_update(self, event):
    if event['event_type'].startswith('agentrun.'):
        self.refresh_agent_runs()
```

### Step 3: Use Database Filtering

```python
# BEFORE: Client-side filtering
filtered_runs = [r for r in runs if r['status'] == 'running']

# AFTER: Database filtering
runs, total = ui_service.get_agent_runs(
    org_id=org_id,
    status_filter='running'
)
```

## 🚨 Error Handling

### Connection Errors

```python
try:
    with db_session_scope() as session:
        # Database operations
        pass
except Exception as e:
    logger.error(f"Database error: {e}")
    # Automatic retry with exponential backoff
```

### Event Delivery Failures

```python
# Webhook delivery with retries
for attempt in range(max_retries):
    try:
        response = await client.post(url, json=payload)
        if response.status_code < 300:
            break
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)
```

## 📊 Monitoring

### Health Checks

```python
# Database health
health = db_manager.health_check()
{
    'status': 'healthy',
    'pool_status': {
        'size': 10,
        'checked_out': 2,
        'overflow': 0
    }
}
```

### Event Metrics

```python
# Event delivery tracking
delivery = WebhookDelivery(
    event_id=event.id,
    success=True,
    status_code=200,
    delivered_at=datetime.utcnow()
)
```

## 🔮 Future Enhancements

### Planned Features

1. **Read Replicas**: Separate read/write database connections
2. **Sharding**: Horizontal scaling for large datasets
3. **Full-Text Search**: PostgreSQL full-text search integration
4. **Metrics Dashboard**: Real-time database and event metrics
5. **Data Archiving**: Automatic archiving of old records

### Extension Points

```python
# Custom event handlers
@event_emitter.on('custom.event')
def handle_custom_event(event):
    # Custom logic
    pass

# Custom middleware
class CustomMiddleware(DatabaseMiddleware):
    def create(self, model_class, data, **kwargs):
        # Custom creation logic
        return super().create(model_class, data, **kwargs)
```

## 📞 Support

For questions or issues:

1. Check the logs: `tail -f logs/database.log`
2. Run health check: `python -c "from codegen.database import get_database_manager; print(get_database_manager().health_check())"`
3. Review event delivery: Check `WebhookDelivery` table for failed deliveries

---

**This database architecture provides a solid foundation for scalable, real-time, event-driven applications while maintaining data consistency and reliability.**

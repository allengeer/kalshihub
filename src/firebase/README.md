# Firebase Module

This module provides Firebase Firestore integration for the Kalshihub application, including data access objects (DAOs) and schema management.

## Collections

### engine_events

Tracks key system events with timestamps and metadata.

**Fields:**
- `event_id` (string): Unique event identifier (primary key)
- `timestamp` (timestamp): Event occurrence timestamp
- `event_name` (string): Name/type of the event
- `event_metadata` (map): JSON metadata for the event

**Usage:**

```python
from firebase.engine_event_dao import EngineEventDAO

# Initialize DAO
dao = EngineEventDAO(project_id="your-project-id")

# Create an event
event = dao.create_event(
    event_name="market_crawl_completed",
    event_metadata={
        "markets_processed": 150,
        "duration_seconds": 12.5,
        "success": True
    }
)

# Get recent events
recent_events = dao.get_recent_events(limit=10)

# Get events by name
crawl_events = dao.get_events_by_name("market_crawl_completed")

# Get events in time range
from datetime import datetime, timedelta
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)
events = dao.get_events_in_range(start_time, end_time)

# Delete old events
deleted_count = dao.delete_old_events(before_time=start_time)
```

### markets

Stores Kalshi prediction market data.

**Fields:**
- `ticker` (string): Unique market identifier (primary key)
- `event_ticker` (string): Event identifier this market belongs to
- `market_type` (string): Type of market
- `title` (string): Market title
- `subtitle` (string): Market subtitle
- `status` (string): Market status (open, closed, settled, etc.)
- `last_price` (number): Last traded price in cents
- `last_price_dollars` (string): Last traded price in dollars
- `volume` (number): Trading volume
- `liquidity` (number): Market liquidity
- `open_time` (timestamp): Market open time
- `close_time` (timestamp): Market close time
- `expiration_time` (timestamp): Market expiration time
- `created_at` (timestamp): Record creation timestamp
- `updated_at` (timestamp): Record last update timestamp
- `crawled_at` (timestamp): Last crawl timestamp
- `data_hash` (string): Hash of market data for change detection

**Usage:**

```python
from firebase.market_dao import MarketDAO

# Initialize DAO
dao = MarketDAO(project_id="your-project-id")

# Batch create/update markets (uses BulkWriter)
from kalshi.service import KalshiAPIService

async with KalshiAPIService() as service:
    markets = await service.getAllOpenMarkets()
    count = dao.batch_create_markets(markets)
    print(f"Processed {count} markets")
```

## Schema Management

The `FirebaseSchemaManager` provides schema definition and validation:

```python
from firebase.schema import FirebaseSchemaManager

# Initialize schema manager
schema_mgr = FirebaseSchemaManager(project_id="your-project-id")

# Get schema definition
schema = schema_mgr.get_schema_definition()

# Deploy schema (creates collections and metadata)
schema_mgr.deploy_schema()

# Validate schema
is_valid = schema_mgr.validate_schema()

# Get schema version
version = schema_mgr.get_schema_version()
```

## Configuration

All DAOs require:
- `project_id`: Firebase project ID
- `credentials_path` (optional): Path to service account JSON file

If `credentials_path` is not provided, default credentials are used (e.g., from `GOOGLE_APPLICATION_CREDENTIALS` environment variable or Google Cloud runtime).

## Best Practices

1. **Event Logging**: Use `EngineEventDAO` to log all significant system events (crawls, errors, state changes)
2. **Metadata**: Include relevant context in `event_metadata` for debugging and analytics
3. **Batch Operations**: Use `batch_create_markets()` for efficient bulk writes with BulkWriter
4. **Cleanup**: Periodically call `delete_old_events()` to remove old event logs
5. **Connection Management**: Always call `dao.close()` when done to cleanup resources

## Event Name Conventions

Use descriptive, hierarchical event names:
- `market_crawl_started`
- `market_crawl_completed`
- `market_crawl_failed`
- `data_validation_error`
- `api_rate_limit_hit`
- `service_started`
- `service_stopped`

## Error Handling

All DAO methods handle Firebase exceptions internally. Check return values:
- `create_event()`: Returns created `EngineEvent`
- `get_event()`: Returns `EngineEvent` or `None` if not found
- `delete_event()`: Returns `True` if deleted, `False` if not found
- `delete_old_events()`: Returns count of deleted events

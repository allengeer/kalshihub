# Firebase Integration Module

This module provides Firebase integration for market data persistence and management.

## Module Structure

```
firebase/
├── __init__.py              # Main module exports
├── market_dao.py            # Data Access Object for market CRUD operations
├── schema.py                # Schema management and deployment
├── job/                     # Scheduled jobs
│   ├── __init__.py
│   └── market_crawler.py    # Market data refresh job
└── service/                 # Business logic services
    └── __init__.py          # (Future services go here)
```

## Components

### Data Access Layer
- **`market_dao.py`**: MarketDAO class for CRUD operations using BulkWriter
  - `batch_create_markets()` - Create/upsert markets in bulk
  - `clear_all_markets()` - Clear all markets using BulkWriter
  - `get_market()` - Retrieve a single market
  - `get_markets_by_status()` - Query markets by status

### Schema Management
- **`schema.py`**: FirebaseSchemaManager for schema deployment and validation
  - `deploy_schema()` - Deploy Firestore schema
  - `validate_schema()` - Validate schema integrity
  - `get_schema_version()` - Get current schema version

### Jobs
- **`job/market_crawler.py`**: MarketCrawler for automated data refresh
  - Uses BulkWriter for efficient bulk operations
  - Implements exponential backoff retry logic
  - Supports scheduled crawling with APScheduler
  - Can run once or on a schedule

### Services
- **`service/`**: Reserved for future business logic services

## Usage

```python
from firebase import MarketDAO, MarketCrawler, FirebaseSchemaManager

# Initialize DAO
dao = MarketDAO(
    project_id="your-project-id",
    credentials_path="path/to/credentials.json"
)

# Create markets using BulkWriter
dao.batch_create_markets(markets)

# Start market crawler
crawler = MarketCrawler(
    firebase_project_id="your-project-id",
    firebase_credentials_path="path/to/credentials.json",
    interval_minutes=30
)
await crawler.run_once()
```

## Key Features

- **BulkWriter Operations**: All bulk operations use Firestore's BulkWriter for optimal performance
- **Real-time Progress**: Progress indicators for long-running operations
- **Exponential Backoff**: Automatic retry logic with exponential backoff
- **Type Safety**: Full type hints throughout
- **Error Handling**: Comprehensive error handling and logging

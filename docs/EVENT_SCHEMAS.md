# Event Schemas

This document describes the event schema standard and all event types used in KalshiHub.

## Standard Event Schema

All events published to Pub/Sub follow this standard schema:

```json
{
  "event_id": "uuid",
  "event_type": "event.category.action",
  "timestamp": "ISO8601",
  "source": "component-name",
  "version": "1.0",
  "metadata": {},
  "correlation_id": "optional-uuid"
}
```

### Fields

- **event_id**: Unique identifier for this event instance (UUID)
- **event_type**: Dot-separated event type (category.action)
- **timestamp**: ISO8601 formatted timestamp
- **source**: Component/service that generated the event
- **version**: Schema version (currently "1.0")
- **metadata**: Event-specific data (structure varies by event type)
- **correlation_id**: Optional UUID for tracking related events

## Event Types

### Market Lifecycle Events

Published to: `market-events`

#### market.created
Published when a new market is discovered/created.

```json
{
  "event_type": "market.created",
  "metadata": {
    "ticker": "NASDAQ-100-2024",
    "event_ticker": "EVENT-2024",
    "status": "initialized",
    "market_type": "binary"
  }
}
```

#### market.updated
Published when market data changes (price, volume, status, etc.).

```json
{
  "event_type": "market.updated",
  "metadata": {
    "ticker": "NASDAQ-100-2024",
    "changes": {
      "status": {"from": "open", "to": "closed"},
      "last_price": {"from": 50, "to": 55}
    }
  }
}
```

#### market.closed
Published when a market closes for trading.

```json
{
  "event_type": "market.closed",
  "metadata": {
    "ticker": "NASDAQ-100-2024",
    "close_time": "2024-12-31T23:59:59Z"
  }
}
```

#### market.settled
Published when a market settles with a result.

```json
{
  "event_type": "market.settled",
  "metadata": {
    "ticker": "NASDAQ-100-2024",
    "result": "yes",
    "settlement_value": 100
  }
}
```

#### market.stale
Published when a market is detected as stale (not updated recently).

```json
{
  "event_type": "market.stale",
  "metadata": {
    "ticker": "NASDAQ-100-2024",
    "last_updated": "2024-01-01T12:00:00Z",
    "stale_duration_minutes": 10
  }
}
```

### Crawler Events

Published to: `crawler-events`

#### crawler.started
Published when a crawl operation begins.

```json
{
  "event_type": "crawler.started",
  "source": "market-crawler",
  "metadata": {
    "operation": "full_crawl" | "filtered_crawl",
    "max_close_ts": 1234567890  // optional, for filtered crawl
  },
  "correlation_id": "uuid"
}
```

#### crawler.completed
Published when a crawl operation completes successfully.

```json
{
  "event_type": "crawler.completed",
  "source": "market-crawler",
  "metadata": {
    "operation": "full_crawl" | "filtered_crawl",
    "total_markets": 1000,
    "success_count": 995,
    "max_close_ts": 1234567890  // optional
  },
  "correlation_id": "uuid"
}
```

#### crawler.failed
Published when a crawl operation fails.

```json
{
  "event_type": "crawler.failed",
  "source": "market-crawler",
  "metadata": {
    "operation": "full_crawl" | "filtered_crawl",
    "error": "Error message",
    "error_type": "ExceptionClassName",
    "max_close_ts": 1234567890  // optional
  },
  "correlation_id": "uuid"
}
```

#### crawler.batch_completed
Published when a batch of markets is processed (future).

```json
{
  "event_type": "crawler.batch_completed",
  "metadata": {
    "batch_size": 100,
    "processed": 98,
    "batch_number": 1,
    "total_batches": 10
  }
}
```

### System Events

Published to: `system-events`

#### system.health_check
Published for health monitoring.

```json
{
  "event_type": "system.health_check",
  "metadata": {
    "component": "market-crawler",
    "status": "healthy",
    "uptime_seconds": 3600
  }
}
```

#### system.error
Published for system-level errors.

```json
{
  "event_type": "system.error",
  "metadata": {
    "component": "market-crawler",
    "error": "Error message",
    "severity": "critical" | "warning" | "info"
  }
}
```

#### system.metric
Published for performance/usage metrics.

```json
{
  "event_type": "system.metric",
  "metadata": {
    "metric_name": "api_latency_ms",
    "value": 150,
    "unit": "milliseconds"
  }
}
```

## Event Consumption

### Push Subscriptions

Events are delivered directly to Cloud Functions via push subscriptions:

- **market-events** → `market-processor` function (future)
- **crawler-events** → `crawler-monitor` function (future)

### Pull Subscriptions

For batch processing, analytics, and reporting:

- **market-events** → Analytics processor (pull)
- **system-events** → Metrics aggregator (pull)

## Event Retention

- Default retention: 7 days (configurable up to 31 days)
- Dead letter topics: For failed processing (future)

## Correlation IDs

Correlation IDs are used to track related events across a single operation. For example, all events from a single crawl operation share the same `correlation_id`, allowing traceability from start to completion.

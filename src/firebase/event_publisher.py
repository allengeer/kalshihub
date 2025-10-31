"""Event publisher for Pub/Sub events."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import pubsub_v1


class EventPublisher:
    """Publisher for events to Google Cloud Pub/Sub topics."""

    EVENT_VERSION = "1.0"
    MAX_BATCH_SIZE = 1000

    def __init__(self, project_id: str):
        """Initialize Event Publisher.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self._publisher: Optional[pubsub_v1.PublisherClient] = None

    def _get_publisher(self) -> pubsub_v1.PublisherClient:
        """Get or create Pub/Sub publisher client.

        Returns:
            Publisher client instance
        """
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    def _create_event(
        self,
        event_type: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create standardized event dictionary.

        Args:
            event_type: Type of event (e.g., "market.updated")
            source: Source of the event (e.g., "market-crawler")
            metadata: Optional event-specific metadata
            correlation_id: Optional correlation ID for tracking flows

        Returns:
            Event dictionary with standardized schema
        """
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "version": self.EVENT_VERSION,
            "metadata": metadata or {},
            "correlation_id": correlation_id,
        }

    def publish_event(
        self,
        topic_name: str,
        event_type: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Publish a single event to a Pub/Sub topic.

        Args:
            topic_name: Name of the Pub/Sub topic
            event_type: Type of event (e.g., "market.updated")
            source: Source of the event (e.g., "market-crawler")
            metadata: Optional event-specific metadata
            correlation_id: Optional correlation ID for tracking flows

        Returns:
            Message ID from Pub/Sub

        Raises:
            Exception: If publishing fails
        """
        publisher = self._get_publisher()
        topic_path = publisher.topic_path(self.project_id, topic_name)

        event = self._create_event(event_type, source, metadata, correlation_id)
        event_json = json.dumps(event).encode("utf-8")

        future = publisher.publish(topic_path, event_json)
        message_id: str = future.result(timeout=30.0)

        return message_id

    def publish_events_batch(
        self,
        topic_name: str,
        events: List[Dict[str, Any]],
    ) -> List[str]:
        """Publish multiple events in a batch to a Pub/Sub topic.

        Args:
            topic_name: Name of the Pub/Sub topic
            events: List of event dictionaries with event_type, source, metadata

        Returns:
            List of message IDs from Pub/Sub

        Raises:
            Exception: If publishing fails
        """
        publisher = self._get_publisher()
        topic_path = publisher.topic_path(self.project_id, topic_name)

        message_ids = []
        # Process in batches of MAX_BATCH_SIZE
        for i in range(0, len(events), self.MAX_BATCH_SIZE):
            batch = events[i : i + self.MAX_BATCH_SIZE]
            futures = []

            for event_data in batch:
                # If event_data is already a dict with event_type, use it directly
                # Otherwise, assume it needs to be wrapped
                if "event_type" in event_data and "source" in event_data:
                    event = self._create_event(
                        event_type=event_data["event_type"],
                        source=event_data["source"],
                        metadata=event_data.get("metadata"),
                        correlation_id=event_data.get("correlation_id"),
                    )
                else:
                    # Backward compatibility - assume event_data is metadata
                    raise ValueError(
                        "Event data must include 'event_type' and 'source' fields"
                    )

                event_json = json.dumps(event).encode("utf-8")
                future = publisher.publish(topic_path, event_json)
                futures.append(future)

            # Wait for all publishes in this batch to complete
            for future in futures:
                message_id = future.result(timeout=30.0)
                message_ids.append(message_id)

        return message_ids

    def publish_market_event(
        self,
        event_type: str,
        metadata: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        """Convenience method to publish a market lifecycle event.

        Args:
            event_type: Market event type (e.g., "market.created", "market.updated")
            metadata: Event metadata (should include ticker, etc.)
            correlation_id: Optional correlation ID

        Returns:
            Message ID from Pub/Sub
        """
        return self.publish_event(
            topic_name="market-events",
            event_type=event_type,
            source="market-crawler",
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def publish_crawler_event(
        self,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Convenience method to publish a crawler operation event.

        Args:
            event_type: Crawler event type
                (e.g., "crawler.started", "crawler.completed")
            metadata: Event metadata
            correlation_id: Optional correlation ID

        Returns:
            Message ID from Pub/Sub
        """
        return self.publish_event(
            topic_name="crawler-events",
            event_type=event_type,
            source="market-crawler",
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def publish_system_event(
        self,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Convenience method to publish a system event.

        Args:
            event_type: System event type (e.g., "system.error", "system.metric")
            metadata: Event metadata
            correlation_id: Optional correlation ID

        Returns:
            Message ID from Pub/Sub
        """
        return self.publish_event(
            topic_name="system-events",
            event_type=event_type,
            source="market-crawler",
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def publish_trading_event(
        self,
        event_type: str,
        metadata: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        """Convenience method to publish a trading event.

        Args:
            event_type: Trading event type
                (e.g., "order.placed", "position.opened", "risk.limit_breached")
            metadata: Event metadata
            correlation_id: Optional correlation ID

        Returns:
            Message ID from Pub/Sub
        """
        return self.publish_event(
            topic_name="trading-events",
            event_type=event_type,
            source="execution-engine",
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def close(self):
        """Close publisher connection."""
        if self._publisher:
            self._publisher.close()
            self._publisher = None

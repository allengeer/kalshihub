"""Tests for Event Publisher."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.firebase.event_publisher import EventPublisher


class TestEventPublisher:
    """Test cases for EventPublisher."""

    @pytest.fixture
    def publisher(self):
        """Create an EventPublisher instance for testing."""
        return EventPublisher(project_id="test-project")

    def test_initialization(self, publisher):
        """Test publisher initialization."""
        assert publisher.project_id == "test-project"
        assert publisher._publisher is None

    @patch("src.firebase.event_publisher.pubsub_v1.PublisherClient")
    def test_publish_event(self, mock_publisher_client, publisher):
        """Test publishing a single event."""
        mock_client = MagicMock()
        mock_publisher_client.return_value = mock_client
        mock_future = MagicMock()
        mock_future.result.return_value = "message-id-123"
        mock_client.topic_path.return_value = "projects/test-project/topics/test-topic"
        mock_client.publish.return_value = mock_future

        message_id = publisher.publish_event(
            topic_name="test-topic",
            event_type="test.event",
            source="test-source",
            metadata={"key": "value"},
        )

        assert message_id == "message-id-123"
        mock_client.publish.assert_called_once()
        # Verify the published message is valid JSON
        call_args = mock_client.publish.call_args
        published_data = json.loads(call_args[0][1].decode("utf-8"))
        assert published_data["event_type"] == "test.event"
        assert published_data["source"] == "test-source"
        assert published_data["metadata"] == {"key": "value"}
        assert "event_id" in published_data
        assert "timestamp" in published_data
        assert published_data["version"] == "1.0"

    @patch("src.firebase.event_publisher.pubsub_v1.PublisherClient")
    def test_publish_market_event(self, mock_publisher_client, publisher):
        """Test convenience method for market events."""
        mock_client = MagicMock()
        mock_publisher_client.return_value = mock_client
        mock_future = MagicMock()
        mock_future.result.return_value = "message-id-456"
        mock_client.topic_path.return_value = (
            "projects/test-project/topics/market-events"
        )
        mock_client.publish.return_value = mock_future

        message_id = publisher.publish_market_event(
            event_type="market.created",
            metadata={"ticker": "TEST-2024"},
        )

        assert message_id == "message-id-456"
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "projects/test-project/topics/market-events"

    @patch("src.firebase.event_publisher.pubsub_v1.PublisherClient")
    def test_publish_crawler_event(self, mock_publisher_client, publisher):
        """Test convenience method for crawler events."""
        mock_client = MagicMock()
        mock_publisher_client.return_value = mock_client
        mock_future = MagicMock()
        mock_future.result.return_value = "message-id-789"
        mock_client.topic_path.return_value = (
            "projects/test-project/topics/crawler-events"
        )
        mock_client.publish.return_value = mock_future

        message_id = publisher.publish_crawler_event(
            event_type="crawler.started",
            metadata={"operation": "full_crawl"},
            correlation_id="corr-123",
        )

        assert message_id == "message-id-789"
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "projects/test-project/topics/crawler-events"
        published_data = json.loads(call_args[0][1].decode("utf-8"))
        assert published_data["correlation_id"] == "corr-123"

    def test_close(self, publisher):
        """Test closing the publisher."""
        mock_publisher = MagicMock()
        publisher._publisher = mock_publisher
        publisher.close()
        mock_publisher.close.assert_called_once()
        assert publisher._publisher is None

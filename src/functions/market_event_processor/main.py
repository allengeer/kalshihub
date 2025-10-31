"""Google Cloud Function for processing Firestore document changes.

This function is triggered when documents are written to Firestore and
publishes appropriate Pub/Sub events based on the change type and document data.
"""

import os
from typing import Any, Optional

import functions_framework
from google.cloud.firestore import DocumentSnapshot
from google.events.cloud.firestore import DocumentEventData

# Import event publisher - handle both direct and relative imports
try:
    from src.firebase.event_publisher import EventPublisher
except ImportError:
    from firebase.event_publisher import EventPublisher  # type: ignore[no-redef]


@functions_framework.cloud_event
def process_market_event(cloud_event: Any) -> None:
    """Process Firestore document change and publish appropriate events.

    This function is triggered by Firestore document writes and publishes
    events to Pub/Sub based on the change type and document data.

    Args:
        cloud_event: CloudEvent containing Firestore document change data
    """
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not firebase_project_id:
        print("ERROR: FIREBASE_PROJECT_ID environment variable not set")
        return

    try:
        # Parse the Firestore event data
        event_data = DocumentEventData.from_json(cloud_event.data)
        value = event_data.value  # DocumentSnapshot

        if not value:
            print("No document value in event data")
            return

        # Extract document path to determine collection
        document_path = value.name if hasattr(value, "name") else str(value)
        collection_name = _extract_collection_from_path(document_path)

        # Only process markets collection for now
        if collection_name != "markets":
            print(f"Skipping collection: {collection_name}")
            return

        # Initialize event publisher
        event_publisher = EventPublisher(project_id=firebase_project_id)

        # Determine change type and process accordingly
        old_value = event_data.old_value  # Previous document state (None for CREATE)
        change_type = _determine_change_type(old_value, value)

        # Process based on change type
        if change_type == "CREATE":
            _publish_market_created(value, event_publisher)
        elif change_type == "UPDATE":
            _publish_market_updated(old_value, value, event_publisher)
        elif change_type == "DELETE":
            # Markets are typically not deleted, but handle it if needed
            print(f"Market deleted: {value.id if hasattr(value, 'id') else 'unknown'}")
            # Could publish market.deleted event if needed in future

        print(f"Successfully processed {change_type} event for market document")

    except Exception as e:
        print(f"ERROR processing Firestore event: {e}")
        raise


def _extract_collection_from_path(document_path: str) -> str:
    """Extract collection name from Firestore document path.

    Args:
        document_path: Full document path
            (e.g., "projects/.../databases/.../documents/markets/TICKER")

    Returns:
        Collection name (e.g., "markets")
    """
    # Path format: projects/{project}/databases/{db}/documents/{collection}/{doc_id}
    parts = document_path.split("/")
    try:
        # Find "documents" and return the next part (collection name)
        documents_index = parts.index("documents")
        if documents_index + 1 < len(parts):
            return parts[documents_index + 1]
    except ValueError:
        pass
    # Fallback: try to extract from path directly
    if "/markets/" in document_path:
        return "markets"
    return "unknown"


def _determine_change_type(
    old_value: Optional[DocumentSnapshot], new_value: DocumentSnapshot
) -> str:
    """Determine the type of Firestore document change.

    Args:
        old_value: Previous document state (None for CREATE)
        new_value: New document state (None for DELETE)

    Returns:
        Change type: "CREATE", "UPDATE", or "DELETE"
    """
    if old_value is None and new_value is not None:
        return "CREATE"
    elif old_value is not None and new_value is None:
        return "DELETE"
    elif old_value is not None and new_value is not None:
        return "UPDATE"
    else:
        # This shouldn't happen, but default to UPDATE
        return "UPDATE"


def _publish_market_created(
    document: DocumentSnapshot, event_publisher: EventPublisher
) -> None:
    """Publish market.created event when a new market document is created.

    Args:
        document: New market document snapshot
        event_publisher: EventPublisher instance
    """
    doc_data = document.to_dict() or {}
    ticker = document.id

    metadata = {
        "ticker": ticker,
        "event_ticker": doc_data.get("event_ticker"),
        "market_type": doc_data.get("market_type"),
        "status": doc_data.get("status"),
        "open_time": _format_timestamp(doc_data.get("open_time")),
        "close_time": _format_timestamp(doc_data.get("close_time")),
        "settle_time": _format_timestamp(doc_data.get("settlement_time")),
        "category": doc_data.get("category"),
    }

    try:
        event_publisher.publish_market_event(
            event_type="market.created",
            metadata=metadata,
        )
        print(f"Published market.created event for {ticker}")
    except Exception as e:
        print(f"ERROR publishing market.created event: {e}")
        raise


def _publish_market_updated(
    old_document: Optional[DocumentSnapshot],
    new_document: DocumentSnapshot,
    event_publisher: EventPublisher,
) -> None:
    """Publish market.updated event when a market document is updated.

    Also publishes market.closed or market.settled if status/result
    changed appropriately.

    Args:
        old_document: Previous document state
        new_document: New document state
        event_publisher: EventPublisher instance
    """
    old_data = old_document.to_dict() if old_document else {}
    new_data = new_document.to_dict() or {}
    ticker = new_document.id

    # Determine what changed
    changes = {}
    status_changed = False

    # Check for status change
    old_status = old_data.get("status")
    new_status = new_data.get("status")
    if old_status != new_status:
        status_changed = True
        changes["status"] = {"from": old_status, "to": new_status}

    # Check for other significant field changes
    significant_fields = [
        "last_price",
        "last_price_dollars",
        "volume_24h",
        "yes_bid",
        "yes_ask",
        "no_bid",
        "no_ask",
    ]

    for field in significant_fields:
        old_val = old_data.get(field)
        new_val = new_data.get(field)
        if old_val != new_val:
            changes[field] = {"from": old_val, "to": new_val}

    # Publish market.updated event
    if changes:
        metadata = {
            "ticker": ticker,
            "changes": changes,
        }

        try:
            event_publisher.publish_market_event(
                event_type="market.updated",
                metadata=metadata,
            )
            print(f"Published market.updated event for {ticker}")
        except Exception as e:
            print(f"ERROR publishing market.updated event: {e}")
            raise

    # Check if market was closed
    if status_changed and new_status in ["closed", "halted"]:
        metadata = {
            "ticker": ticker,
            "close_time": _format_timestamp(new_data.get("close_time")),
        }

        try:
            event_publisher.publish_market_event(
                event_type="market.closed",
                metadata=metadata,
            )
            print(f"Published market.closed event for {ticker}")
        except Exception as e:
            print(f"ERROR publishing market.closed event: {e}")

    # Check if market was settled (result field set and changed)
    old_result = old_data.get("result")
    new_result = new_data.get("result")
    if new_result and new_result != old_result and new_result in ["yes", "no"]:
        metadata = {
            "ticker": ticker,
            "result": new_result,
            "settlement_value_cents": new_data.get("settlement_value"),
            "settlement_time": _format_timestamp(new_data.get("settlement_time")),
        }

        try:
            event_publisher.publish_market_event(
                event_type="market.settled",
                metadata=metadata,
            )
            print(f"Published market.settled event for {ticker}")
        except Exception as e:
            print(f"ERROR publishing market.settled event: {e}")


def _format_timestamp(timestamp: Any) -> Optional[str]:
    """Format Firestore timestamp to ISO8601 string.

    Args:
        timestamp: Firestore timestamp object or None

    Returns:
        ISO8601 formatted string or None
    """
    if timestamp is None:
        return None

    # Handle Firestore Timestamp objects
    if hasattr(timestamp, "isoformat"):
        result: Optional[str] = timestamp.isoformat()
        return result
    elif hasattr(timestamp, "timestamp"):
        # Firestore Timestamp has timestamp() method
        from datetime import datetime

        result = datetime.fromtimestamp(timestamp.timestamp()).isoformat() + "Z"
        return result
    else:
        # Fallback to string conversion
        result = str(timestamp)
        return result if result else None

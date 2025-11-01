"""Google Cloud Function for processing Firestore document changes.

This function is triggered when documents are written to Firestore and
publishes appropriate Pub/Sub events based on the change type and document data.
"""

import os
from typing import Any, Dict, Optional

import functions_framework
from cloudevents.http import CloudEvent
from firestoredata.types import MutableMapping, Value
from google.events.cloud import firestore as firestoredata

# Import event publisher - handle both direct and relative imports
try:
    from src.firebase.event_publisher import EventPublisher
except ImportError:
    from firebase.event_publisher import EventPublisher  # type: ignore[no-redef]


@functions_framework.cloud_event
def process_market_event(cloud_event: CloudEvent) -> None:
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
        firestore_payload = firestoredata.DocumentEventData()
        firestore_payload._pb.ParseFromString(cloud_event.data)
        # Extract document information
        # The event data structure: {"value": {...}, "oldValue": {...}}
        value = firestore_payload.value.fields
        old_value = firestore_payload.old_value.fields

        # Extract document name/path from the DocumentSnapshot, not from fields
        document_name = (
            firestore_payload.value.name if firestore_payload.value.name else ""
        )
        if not document_name:
            # Try alternative path from cloud_event source
            if hasattr(cloud_event, "source"):
                document_name = cloud_event.source or ""
            else:
                document_name = ""

        collection_name = _extract_collection_from_path(document_name)

        # Only process markets collection for now
        if collection_name != "markets":
            print(f"Skipping collection: {collection_name}")
            return

        # Initialize event publisher
        event_publisher = EventPublisher(project_id=firebase_project_id)

        # Determine change type
        change_type = _determine_change_type_from_dict(old_value, value)

        # Extract ticker from document name (it's the document ID)
        ticker = _extract_document_id(document_name)

        # Process based on change type
        if change_type == "CREATE":
            _publish_market_created_from_dict(value, ticker, event_publisher)
        elif change_type == "UPDATE":
            _publish_market_updated_from_dict(old_value, value, ticker, event_publisher)
        elif change_type == "DELETE":
            # Markets are typically not deleted, but handle it if needed
            print(f"Market deleted: {ticker}")
            # Could publish market.deleted event if needed in future

        print(f"Successfully processed {change_type} event for market {ticker}")

    except Exception as e:
        print(f"ERROR processing Firestore event: {e}")
        import traceback

        traceback.print_exc()
        # Don't raise - allow function to complete to avoid retries on parsing errors
        return


def _extract_collection_from_path(document_path: str) -> str:
    """Extract collection name from Firestore document path.

    Args:
        document_path: Full document path
            (e.g., "projects/.../databases/.../documents/markets/TICKER")

    Returns:
        Collection name (e.g., "markets")
    """
    if not document_path:
        return "unknown"

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


def _extract_document_id(document_path: str) -> str:
    """Extract document ID from Firestore document path.

    Args:
        document_path: Full document path

    Returns:
        Document ID (ticker)
    """
    if not document_path:
        return "unknown"

    parts = document_path.split("/")
    try:
        documents_index = parts.index("documents")
        if documents_index + 2 < len(parts):
            return parts[documents_index + 2]  # Collection is +1, doc_id is +2
    except (ValueError, IndexError):
        pass

    # Fallback: try to get last part after /markets/
    if "/markets/" in document_path:
        return document_path.split("/markets/")[-1].split("/")[0]

    return "unknown"


def _determine_change_type_from_dict(
    old_value: MutableMapping[str, Value], new_value: MutableMapping[str, Value]
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


def _publish_market_created_from_dict(
    fields: MutableMapping[str, Value], ticker: str, event_publisher: EventPublisher
) -> None:
    """Publish market.created event when a new market document is created.

    Args:
        document_dict: New market document data
        ticker: Market ticker (document ID)
        event_publisher: EventPublisher instance
    """
    metadata = {
        "ticker": ticker,
        "event_ticker": _get_field_value(fields, "event_ticker"),
        "market_type": _get_field_value(fields, "market_type"),
        "status": _get_field_value(fields, "status"),
        "open_time": _format_firestore_timestamp(_get_field_value(fields, "open_time")),
        "close_time": _format_firestore_timestamp(
            _get_field_value(fields, "close_time")
        ),
        "settle_time": _format_firestore_timestamp(
            _get_field_value(fields, "settlement_time")
        ),
        "category": _get_field_value(fields, "category"),
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


def _publish_market_updated_from_dict(
    old_fields: MutableMapping[str, Value],
    new_fields: MutableMapping[str, Value],
    ticker: str,
    event_publisher: EventPublisher,
) -> None:
    """Publish market.updated event when a market document is updated.

    Also publishes market.closed or market.settled if status/result changed.

    Args:
        old_fields: Previous document state
        new_fields: New document state
        ticker: Market ticker
        event_publisher: EventPublisher instance
    """
    changes = {}
    status_changed = False

    # Check for status change
    old_status = _get_field_value(old_fields, "status")
    new_status = _get_field_value(new_fields, "status")
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
        old_val = _get_field_value(old_fields, field)
        new_val = _get_field_value(new_fields, field)
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
        close_time = _format_firestore_timestamp(
            _get_field_value(new_fields, "close_time")
        )
        closed_metadata: Dict[str, Any] = {
            "ticker": ticker,
            "close_time": close_time or "",
        }

        try:
            event_publisher.publish_market_event(
                event_type="market.closed",
                metadata=closed_metadata,
            )
            print(f"Published market.closed event for {ticker}")
        except Exception as e:
            print(f"ERROR publishing market.closed event: {e}")

    # Check if market was settled (result field set and changed)
    old_result = _get_field_value(old_fields, "result")
    new_result = _get_field_value(new_fields, "result")
    if new_result and new_result != old_result and new_result in ["yes", "no"]:
        settlement_time = _format_firestore_timestamp(
            _get_field_value(new_fields, "settlement_time")
        )
        settled_metadata: Dict[str, Any] = {
            "ticker": ticker,
            "result": new_result,
            "settlement_value_cents": _get_field_value(new_fields, "settlement_value"),
            "settlement_time": settlement_time or "",
        }

        try:
            event_publisher.publish_market_event(
                event_type="market.settled",
                metadata=settled_metadata,
            )
            print(f"Published market.settled event for {ticker}")
        except Exception as e:
            print(f"ERROR publishing market.settled event: {e}")


def _get_field_value(fields: MutableMapping[str, Value], field_name: str) -> Any:
    """Extract field value from Firestore document fields dict.

    Firestore fields can be structured as:
    {"field_name": {"stringValue": "value"}} or
    {"field_name": {"integerValue": 123}} or
    {"field_name": {"timestampValue": "..."}} or
    Or just plain {"field_name": value} if already parsed

    Args:
        fields: Firestore fields dictionary
        field_name: Name of the field to extract

    Returns:
        Field value or None
    """
    if not fields or field_name not in fields:
        return None

    field_data = fields[field_name]

    # If it's already a plain value, return it
    if not isinstance(field_data, dict):
        return field_data

    # Handle Firestore value types
    if "stringValue" in field_data:
        return field_data["stringValue"]
    elif "integerValue" in field_data:
        return int(field_data["integerValue"])
    elif "doubleValue" in field_data:
        return float(field_data["doubleValue"])
    elif "booleanValue" in field_data:
        return field_data["booleanValue"]
    elif "timestampValue" in field_data:
        return field_data["timestampValue"]
    elif "nullValue" in field_data:
        return None
    else:
        # Unknown type, try to return as-is
        return field_data


def _format_firestore_timestamp(timestamp_value: Any) -> Optional[str]:
    """Format Firestore timestamp to ISO8601 string.

    Args:
        timestamp_value: Firestore timestamp (string, dict, or None)

    Returns:
        ISO8601 formatted string or None
    """
    if timestamp_value is None:
        return None

    # If it's already a string, return it
    if isinstance(timestamp_value, str):
        # Ensure it ends with Z if it's an ISO string
        if timestamp_value.endswith("Z"):
            return timestamp_value
        return timestamp_value + "Z" if "T" in timestamp_value else timestamp_value

    # If it's a dict with timestampValue
    if isinstance(timestamp_value, dict):
        ts = timestamp_value.get("timestampValue")
        if ts:
            return ts if isinstance(ts, str) else str(ts)

    # Fallback to string conversion
    return str(timestamp_value)

"""Google Cloud Function for processing Firestore document changes.

This function is triggered when documents are written to Firestore and
publishes appropriate Pub/Sub events based on the change type and document data.
"""

import os
from typing import Any, Dict, Optional

import functions_framework
from cloudevents.http import CloudEvent
from firebase_admin import firestore
from google.cloud.firestore_v1.types import Value
from google.cloud.firestore_v1.types.document import MutableMapping
from google.events.cloud import firestore as firestoredata

# Import event publisher - handle both direct and relative imports
try:
    from src.firebase.event_publisher import EventPublisher
    from src.firebase.market_dao import MarketDAO
    from src.firebase.orderbook_dao import OrderbookDAO
    from src.kalshi.service import KalshiAPIService
except ImportError:
    from firebase.event_publisher import EventPublisher  # type: ignore[no-redef]
    from firebase.market_dao import MarketDAO  # type: ignore[no-redef]
    from firebase.orderbook_dao import OrderbookDAO  # type: ignore[no-redef]
    from kalshi.service import KalshiAPIService  # type: ignore[no-redef]


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
            # Check if score-based orderbook update is needed
            _maybe_update_score_with_orderbook(
                change_type, ticker, None, value, firebase_project_id
            )
        elif change_type == "UPDATE":
            _publish_market_updated_from_dict(old_value, value, ticker, event_publisher)
            # Check if score-based orderbook update is needed
            _maybe_update_score_with_orderbook(
                change_type, ticker, old_value, value, firebase_project_id
            )
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
        old_value: Previous document state (empty mapping for CREATE)
        new_value: New document state (empty mapping for DELETE)

    Returns:
        Change type: "CREATE", "UPDATE", or "DELETE"
    """
    # Check if mappings are empty (not just None, since .fields returns MutableMapping)
    old_is_empty = not old_value or len(old_value) == 0
    new_is_empty = not new_value or len(new_value) == 0

    if old_is_empty and not new_is_empty:
        return "CREATE"
    elif not old_is_empty and new_is_empty:
        return "DELETE"
    elif not old_is_empty and not new_is_empty:
        return "UPDATE"
    else:
        # Both empty - shouldn't happen, but default to UPDATE
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
    Or as a protobuf Value object with snake_case attributes

    Args:
        fields: Firestore fields dictionary
        field_name: Name of the field to extract

    Returns:
        Field value or None
    """
    if not fields or field_name not in fields:
        return None

    field_data = fields[field_name]

    # If it's already a plain value (int, float, str, etc.), return it
    if isinstance(field_data, (int, float, str, bool, type(None))):
        return field_data

    # Handle protobuf Value object with snake_case attributes
    if hasattr(field_data, "double_value"):
        return float(field_data.double_value)
    elif hasattr(field_data, "integer_value"):
        return int(field_data.integer_value)
    elif hasattr(field_data, "string_value"):
        return field_data.string_value
    elif hasattr(field_data, "boolean_value"):
        return field_data.boolean_value
    elif hasattr(field_data, "timestamp_value"):
        return field_data.timestamp_value
    elif hasattr(field_data, "null_value"):
        return None

    # Handle dict-based Firestore value types (camelCase)
    if isinstance(field_data, dict):
        if "stringValue" in field_data:
            return field_data["stringValue"]
        elif "integerValue" in field_data:
            return int(field_data["integerValue"])
        elif "doubleValue" in field_data:
            return float(field_data["doubleValue"])
        elif "double_value" in field_data:  # Also check snake_case in dict
            return float(field_data["double_value"])
        elif "booleanValue" in field_data:
            return field_data["booleanValue"]
        elif "timestampValue" in field_data:
            return field_data["timestampValue"]
        elif "nullValue" in field_data:
            return None

    # Unknown type, try to return as-is or convert to string for debugging
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


def _maybe_update_score_with_orderbook(
    change_type: str,
    ticker: str,
    old_fields: Optional[MutableMapping[str, Value]],
    new_fields: MutableMapping[str, Value],
    firebase_project_id: str,
) -> None:
    """Update market score with orderbook data if score conditions are met.

    For CREATE: triggers when score > 0.1
    For UPDATE: triggers when score crosses from < 0.1 to >= 0.1

    Args:
        change_type: "CREATE" or "UPDATE"
        ticker: Market ticker
        old_fields: Previous document state (None for CREATE)
        new_fields: New document state
        firebase_project_id: Firebase project ID
    """
    try:
        # Extract score from new fields
        new_score = _get_field_value(new_fields, "score")
        if new_score is None:
            return

        # Convert to float if needed
        if isinstance(new_score, (int, float)):
            new_score_float = float(new_score)
        else:
            try:
                new_score_float = float(new_score)
            except (ValueError, TypeError):
                print(f"Could not parse score for {ticker}: {new_score}")
                return

        # Check conditions based on change type
        should_update = False

        if change_type == "CREATE":
            # For CREATE: trigger if score > 0.1
            if new_score_float > 0.1:
                should_update = True
                print(
                    f"CREATE: Market {ticker} has score {new_score_float:.4f} > 0.1, "
                    "fetching orderbook"
                )
        elif change_type == "UPDATE":
            # Skip if this update is only from an orderbook update (to prevent loops)
            # Check if only orderbook-related fields or updated_at changed
            orderbook_fields = {
                "score_orderbook",
                "taker_potential_orderbook",
                "maker_potential_orderbook",
                "updated_at",
            }

            # Get list of changed fields
            changed_fields = set()
            if old_fields:
                # Fields that exist in new but not old, or have different values
                for field_name in new_fields:
                    old_value = _get_field_value(old_fields, field_name)
                    new_value = _get_field_value(new_fields, field_name)
                    if old_value != new_value:
                        changed_fields.add(field_name)

            # If only orderbook fields changed, skip to prevent loop
            if changed_fields and changed_fields.issubset(orderbook_fields):
                print(
                    f"UPDATE: Skipping orderbook fetch for {ticker} - "
                    f"only orderbook fields changed: {changed_fields}"
                )
                return

            # For UPDATE: trigger if score crossed from < 0.1 to >= 0.1
            old_score = _get_field_value(old_fields, "score") if old_fields else None
            if old_score is not None:
                try:
                    if isinstance(old_score, (int, float)):
                        old_score_float = float(old_score)
                    else:
                        old_score_float = float(old_score)
                except (ValueError, TypeError):
                    old_score_float = None
            else:
                old_score_float = None

            if old_score_float is not None:
                # Only trigger if score crossed from < 0.1 to >= 0.1
                if old_score_float < 0.1 and new_score_float >= 0.1:
                    should_update = True
                    print(
                        f"UPDATE: Market {ticker} score crossed from "
                        f"{old_score_float:.4f} to {new_score_float:.4f}, "
                        "fetching orderbook"
                    )
            elif new_score_float >= 0.1:
                # If old score was None but new score >= 0.1, also update
                should_update = True
                print(
                    f"UPDATE: Market {ticker} has score {new_score_float:.4f} >= 0.1 "
                    "(old score was None), fetching orderbook"
                )

        if not should_update:
            return

        # Fetch orderbook and update market
        _update_market_score_with_orderbook(ticker, firebase_project_id)

    except Exception as e:
        print(f"ERROR checking score conditions for {ticker}: {e}")
        import traceback

        traceback.print_exc()


async def _fetch_orderbook_and_update_market(
    ticker: str, firebase_project_id: str
) -> None:
    """Fetch orderbook and update market scores asynchronously.

    Args:
        ticker: Market ticker
        firebase_project_id: Firebase project ID
    """
    try:
        # Initialize services
        # Use async context manager to ensure proper cleanup of HTTP client
        async with KalshiAPIService() as kalshi_service:
            market_dao = MarketDAO(
                project_id=firebase_project_id,
                credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH"),
            )
            orderbook_dao = OrderbookDAO(
                project_id=firebase_project_id,
                credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH"),
            )

            # Get current market
            market = market_dao.get_market(ticker)
            if not market:
                print(f"Market {ticker} not found in database")
                return

            # Fetch orderbook with depth=3
            print(f"Fetching orderbook for {ticker} with depth=3")
            orderbook_response = await kalshi_service.get_market_orderbook(
                ticker, depth=3
            )

            if not orderbook_response or not orderbook_response.orderbook:
                print(f"No orderbook data returned for {ticker}")
                return

            orderbook = orderbook_response.orderbook

            # Log original potentials (before orderbook update)
            original_taker_potential = market.taker_potential
            original_maker_potential = market.maker_potential
            print(
                f"Original potentials for {ticker}: "
                f"taker={original_taker_potential:.4f}, "
                f"maker={original_maker_potential:.4f}"
            )

            # Update market scores with orderbook data
            updated_scores = market.update_score_with_orderbook(
                orderbook_response.orderbook
            )

            # Log updated potentials (after orderbook update)
            updated_taker_potential = updated_scores["taker_potential"]
            updated_maker_potential = updated_scores["maker_potential"]
            print(
                f"Updated potentials for {ticker}: "
                f"taker={updated_taker_potential:.4f}, "
                f"maker={updated_maker_potential:.4f}"
            )

            # Update market object with new scores
            # Note: We can't directly set properties on Market dataclass,
            # so we need to create a new Market object with updated values
            # However, since score, taker_potential, and maker_potential are
            # computed properties, we need to store them separately or
            # update the market in a way that preserves them.

            # Actually, looking at MarketDAO._market_to_dict, it stores score,
            # taker_potential, and maker_potential. But these are computed properties.
            # We need to update the market document directly with the new values.

            # Update the market document with new score values
            db = market_dao._get_db()
            market_ref = db.collection("markets").document(ticker)

            # Get current document to check existing values
            current_doc = market_ref.get()
            current_data = current_doc.to_dict() if current_doc.exists else {}

            # Build update dict - only update fields that actually changed
            # to avoid triggering unnecessary UPDATE events
            update_dict = {
                # Orderbook-based potentials (from deep scan) - always update these
                "taker_potential_orderbook": float(updated_taker_potential),
                "maker_potential_orderbook": float(updated_maker_potential),
                "score_orderbook": float(updated_scores["score_enhanced"]),
                # Update timestamp
                "updated_at": firestore.SERVER_TIMESTAMP,
            }

            # Only update original fields if they're missing or different
            # This prevents triggering UPDATE events when updating orderbook data
            current_score = _get_field_value(
                current_data if isinstance(current_data, dict) else {}, "score"
            )
            current_taker = _get_field_value(
                current_data if isinstance(current_data, dict) else {},
                "taker_potential",
            )
            current_maker = _get_field_value(
                current_data if isinstance(current_data, dict) else {},
                "maker_potential",
            # Store both original (market data) and orderbook-based potentials
            # separately. Original potentials are from market data calculations.
            # Orderbook potentials are from deep scan with orderbook data.
            market_ref.update(
                {
                    # Original potentials (from market data)
                    "taker_potential": float(original_taker_potential),
                    "maker_potential": float(original_maker_potential),
                    "score": float(market.score),  # Original score
                    # Orderbook-based potentials (from deep scan)
                    "taker_potential_orderbook": float(updated_taker_potential),
                    "maker_potential_orderbook": float(updated_maker_potential),
                    "score_orderbook": float(updated_scores["score_enhanced"]),
                    # Update timestamp
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            original_score_float = float(market.score)
            original_taker_float = float(original_taker_potential)
            original_maker_float = float(original_maker_potential)

            # Only update original fields if they're missing or changed
            if current_score is None or float(current_score) != original_score_float:
                update_dict["score"] = original_score_float
            if current_taker is None or float(current_taker) != original_taker_float:
                update_dict["taker_potential"] = original_taker_float
            if current_maker is None or float(current_maker) != original_maker_float:
                update_dict["maker_potential"] = original_maker_float

            market_ref.update(update_dict)

            # Persist orderbook with calculated properties
            orderbook_dao.upsert_orderbook(
                orderbook=orderbook,
                ticker=ticker,
                score=updated_scores["score_enhanced"],
                taker_potential=updated_scores["taker_potential"],
                maker_potential=updated_scores["maker_potential"],
            )

            print(
                f"Updated market {ticker} - Original scores: "
                f"score={market.score:.4f}, "
                f"taker={original_taker_potential:.4f}, "
                f"maker={original_maker_potential:.4f}"
            )
            print(
                f"Updated market {ticker} - Orderbook scores: "
                f"score={updated_scores['score_enhanced']:.4f}, "
                f"taker={updated_taker_potential:.4f}, "
                f"maker={updated_maker_potential:.4f}"
            )
            print(f"Persisted orderbook for {ticker} with calculated properties")

    except Exception as e:
        print(f"ERROR updating market {ticker} with orderbook: {e}")
        import traceback

        traceback.print_exc()


def _update_market_score_with_orderbook(ticker: str, firebase_project_id: str) -> None:
    """Synchronous wrapper to run async orderbook update.

    This function runs the async orderbook fetch and update, handling both
    cases where an event loop may or may not already be running.

    Args:
        ticker: Market ticker
        firebase_project_id: Firebase project ID
    """
    import asyncio
    import concurrent.futures

    async def _run_async_task() -> None:
        """Run the async orderbook update task."""
        await _fetch_orderbook_and_update_market(ticker, firebase_project_id)

    try:
        # Check if there's already a running event loop
        try:
            asyncio.get_running_loop()
            # Event loop is already running - run in a separate thread with new loop
            # This prevents "RuntimeError: This event loop is already running"

            def run_in_new_loop() -> None:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(_run_async_task())
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                future.result()  # Wait for completion
        except RuntimeError:
            # No event loop is running - safe to use asyncio.run()
            asyncio.run(_run_async_task())
    except Exception as e:
        print(f"ERROR running async orderbook update for {ticker}: {e}")
        import traceback

        traceback.print_exc()

"""Market Data Access Object for Firebase Firestore operations."""

import hashlib
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client

# Import Market - handle both direct and relative imports
try:
    from src.kalshi.service import Market
except ImportError:
    from kalshi.service import Market  # type: ignore[no-redef]


class MarketDAO:
    """Data Access Object for Market data in Firebase Firestore."""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """Initialize Market DAO.

        Args:
            project_id: Firebase project ID
            credentials_path: Path to service account credentials JSON file
        """
        if not project_id:
            raise ValueError("Firebase project ID is required")
        self.project_id = project_id
        self.credentials_path = credentials_path
        self._db: Optional[Client] = None
        self._app: Optional[firebase_admin.App] = None

    def _get_db(self) -> Client:
        """Get or create Firestore client."""
        if self._db is None:
            if not firebase_admin._apps:
                if self.credentials_path:
                    cred = credentials.Certificate(self.credentials_path)
                    self._app = firebase_admin.initialize_app(cred)
                else:
                    # Use default credentials (e.g., from environment)
                    self._app = firebase_admin.initialize_app()
            else:
                self._app = firebase_admin.get_app()

            self._db = firestore.client(app=self._app)

        return self._db

    def _calculate_data_hash(self, market: Market) -> str:
        """Calculate hash of market data for change detection.

        Args:
            market: Market object to hash

        Returns:
            SHA256 hash of market data
        """
        # Create a dictionary of all market fields for hashing
        market_data = {
            "ticker": market.ticker,
            "event_ticker": market.event_ticker,
            "market_type": market.market_type,
            "title": market.title,
            "subtitle": market.subtitle,
            "yes_sub_title": market.yes_sub_title,
            "no_sub_title": market.no_sub_title,
            "status": market.status,
            "response_price_units": market.response_price_units,
            "notional_value": market.notional_value,
            "notional_value_dollars": market.notional_value_dollars,
            "tick_size": market.tick_size,
            "yes_bid": market.yes_bid,
            "yes_bid_dollars": market.yes_bid_dollars,
            "yes_ask": market.yes_ask,
            "yes_ask_dollars": market.yes_ask_dollars,
            "no_bid": market.no_bid,
            "no_bid_dollars": market.no_bid_dollars,
            "no_ask": market.no_ask,
            "no_ask_dollars": market.no_ask_dollars,
            "last_price": market.last_price,
            "last_price_dollars": market.last_price_dollars,
            "previous_yes_bid": market.previous_yes_bid,
            "previous_yes_bid_dollars": market.previous_yes_bid_dollars,
            "previous_yes_ask": market.previous_yes_ask,
            "previous_yes_ask_dollars": market.previous_yes_ask_dollars,
            "previous_price": market.previous_price,
            "previous_price_dollars": market.previous_price_dollars,
            "volume": market.volume,
            "volume_24h": market.volume_24h,
            "liquidity": market.liquidity,
            "liquidity_dollars": market.liquidity_dollars,
            "open_interest": market.open_interest,
            "result": market.result,
            "can_close_early": market.can_close_early,
            "expiration_value": market.expiration_value,
            "category": market.category,
            "risk_limit_cents": market.risk_limit_cents,
            "rules_primary": market.rules_primary,
            "rules_secondary": market.rules_secondary,
            "settlement_value": market.settlement_value,
            "settlement_value_dollars": market.settlement_value_dollars,
            "price_level_structure": market.price_level_structure,
            "price_ranges": market.price_ranges,
            "open_time": market.open_time.isoformat(),
            "close_time": market.close_time.isoformat(),
            "expiration_time": market.expiration_time.isoformat(),
            "latest_expiration_time": market.latest_expiration_time.isoformat(),
            "settlement_timer_seconds": market.settlement_timer_seconds,
        }

        # Convert to JSON string and hash
        json_str = json.dumps(market_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _market_to_dict(self, market: Market) -> Dict[str, Any]:
        """Convert Market object to Firestore document dictionary.

        Args:
            market: Market object to convert

        Returns:
            Dictionary representation for Firestore
        """
        now = firestore.SERVER_TIMESTAMP
        data_hash = self._calculate_data_hash(market)

        return {
            "ticker": market.ticker,
            "event_ticker": market.event_ticker,
            "market_type": market.market_type,
            "title": market.title,
            "subtitle": market.subtitle,
            "yes_sub_title": market.yes_sub_title,
            "no_sub_title": market.no_sub_title,
            "status": market.status,
            "response_price_units": market.response_price_units,
            "notional_value": market.notional_value,
            "notional_value_dollars": market.notional_value_dollars,
            "tick_size": market.tick_size,
            "yes_bid": market.yes_bid,
            "yes_bid_dollars": market.yes_bid_dollars,
            "yes_ask": market.yes_ask,
            "yes_ask_dollars": market.yes_ask_dollars,
            "no_bid": market.no_bid,
            "no_bid_dollars": market.no_bid_dollars,
            "no_ask": market.no_ask,
            "no_ask_dollars": market.no_ask_dollars,
            "last_price": market.last_price,
            "last_price_dollars": market.last_price_dollars,
            "previous_yes_bid": market.previous_yes_bid,
            "previous_yes_bid_dollars": market.previous_yes_bid_dollars,
            "previous_yes_ask": market.previous_yes_ask,
            "previous_yes_ask_dollars": market.previous_yes_ask_dollars,
            "previous_price": market.previous_price,
            "previous_price_dollars": market.previous_price_dollars,
            "volume": market.volume,
            "volume_24h": market.volume_24h,
            "liquidity": market.liquidity,
            "liquidity_dollars": market.liquidity_dollars,
            "open_interest": market.open_interest,
            "result": market.result,
            "can_close_early": market.can_close_early,
            "expiration_value": market.expiration_value,
            "category": market.category,
            "risk_limit_cents": market.risk_limit_cents,
            "rules_primary": market.rules_primary,
            "rules_secondary": market.rules_secondary,
            "settlement_value": market.settlement_value,
            "settlement_value_dollars": market.settlement_value_dollars,
            "price_level_structure": market.price_level_structure,
            "price_ranges": market.price_ranges,
            "open_time": market.open_time,
            "close_time": market.close_time,
            "expiration_time": market.expiration_time,
            "latest_expiration_time": market.latest_expiration_time,
            "settlement_timer_seconds": market.settlement_timer_seconds,
            "created_at": now,
            "updated_at": now,
            "crawled_at": now,
            "data_hash": data_hash,
            "score": market.score,  # Calculate and store score for querying/sorting
            "taker_potential": market.taker_potential,  # Store taker potential
            "maker_potential": market.maker_potential,  # Store maker potential
        }

    def create_market(self, market: Market) -> bool:
        """Create a new market in Firestore.

        Args:
            market: Market object to create

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self._get_db()
            market_ref = db.collection("markets").document(market.ticker)
            market_data = self._market_to_dict(market)
            market_ref.set(market_data)
            return True
        except Exception as e:
            print(f"Failed to create market {market.ticker}: {e}")
            return False

    def get_market(self, ticker: str) -> Optional[Market]:
        """Get a market by ticker.

        Args:
            ticker: Market ticker to retrieve

        Returns:
            Market object or None if not found
        """
        try:
            db = self._get_db()
            market_ref = db.collection("markets").document(ticker)
            market_doc = market_ref.get()

            if not market_doc.exists:
                return None
            return self._dict_to_market(market_doc.to_dict())
        except Exception as e:
            print(f"Failed to get market {ticker}: {e}")
            return None

    def update_market(self, market: Market) -> bool:
        """Update an existing market in Firestore.

        Args:
            market: Market object to update

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self._get_db()
            market_ref = db.collection("markets").document(market.ticker)

            # Check if market exists
            if not market_ref.get().exists:
                return False

            market_data = self._market_to_dict(market)
            # Preserve original created_at; do not overwrite on updates
            market_data.pop("created_at", None)
            market_ref.update(market_data)
            return True
        except Exception as e:
            print(f"Failed to update market {market.ticker}: {e}")
            return False

    def delete_market(self, ticker: str) -> bool:
        """Delete a market by ticker.

        Args:
            ticker: Market ticker to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self._get_db()
            market_ref = db.collection("markets").document(ticker)
            market_ref.delete()
            return True
        except Exception as e:
            print(f"Failed to delete market {ticker}: {e}")
            return False

    def batch_create_markets(self, markets: List[Market]) -> int:
        """Create multiple markets using BulkWriter for efficient bulk operations.

        Args:
            markets: List of Market objects to create

        Returns:
            Number of successfully created markets
        """
        if not markets:
            return 0

        try:
            db = self._get_db()
            bulk_writer = db.bulk_writer()
            success_count = 0

            print(f"   Queuing {len(markets)} markets for creation...")
            sys.stdout.flush()

            for i, market in enumerate(markets):
                try:
                    market_ref = db.collection("markets").document(market.ticker)
                    # If existing, update without changing created_at
                    # Else, create with created_at
                    if market_ref.get().exists:
                        market_data = self._market_to_dict(market)
                        market_data.pop("created_at", None)
                        bulk_writer.update(market_ref, market_data)
                    else:
                        market_data = self._market_to_dict(market)
                        bulk_writer.set(market_ref, market_data)
                    success_count += 1

                    # Print progress every 1000 markets
                    if (i + 1) % 1000 == 0:
                        print(f"   Queued {i + 1}/{len(markets)} markets...")
                        sys.stdout.flush()

                except Exception as e:
                    print(f"   Failed to prepare market {market.ticker}: {e}")
                    sys.stdout.flush()

            # Flush all pending operations
            print(f"   Flushing {success_count} create operations...")
            sys.stdout.flush()
            bulk_writer.close()

            print(f"✓ Successfully created {success_count} markets")
            sys.stdout.flush()
            return success_count

        except Exception as e:
            print(f"Batch create failed: {e}")
            sys.stdout.flush()
            return 0

    def batch_update_markets(self, markets: List[Market]) -> int:
        """Update multiple markets in a batch operation.

        Args:
            markets: List of Market objects to update

        Returns:
            Number of successfully updated markets
        """
        if not markets:
            return 0

        try:
            db = self._get_db()
            batch = db.batch()
            success_count = 0

            for market in markets:
                try:
                    market_ref = db.collection("markets").document(market.ticker)
                    market_data = self._market_to_dict(market)
                    # Preserve original created_at during updates
                    market_data.pop("created_at", None)
                    batch.update(market_ref, market_data)
                    success_count += 1
                except Exception as e:
                    print(
                        f"Failed to prepare market {market.ticker} for batch "
                        f"update: {e}"
                    )

            if success_count > 0:
                batch.commit()

            return success_count
        except Exception as e:
            print(f"Batch update failed: {e}")
            return 0

    def get_markets_by_status(self, status: str) -> List[Market]:
        """Get all markets with a specific status.

        Args:
            status: Market status to filter by

        Returns:
            List of Market objects
        """
        try:
            db = self._get_db()
            markets_ref = db.collection("markets").where("status", "==", status)
            markets_docs = markets_ref.stream()

            markets = []
            for doc in markets_docs:
                market = self._dict_to_market(doc.to_dict())
                if market:
                    markets.append(market)

            return markets
        except Exception as e:
            print(f"Failed to get markets by status {status}: {e}")
            return []

    def get_stale_active_market_tickers(self, cutoff_time: datetime) -> List[str]:
        """Get tickers for markets not closed and not updated since cutoff.

        Args:
            cutoff_time: Datetime; markets with updated_at older than this are stale

        Returns:
            List of market tickers needing refresh
        """
        try:
            db = self._get_db()
            # Firestore limitation: avoid "!=" on status with another range filter
            # Query for active statuses explicitly
            active_statuses = ["initialized", "active", "settled", "determined"]
            query = (
                db.collection("markets")
                .where("status", "in", active_statuses)
                .where("updated_at", "<", cutoff_time)
                .order_by("updated_at")
            )

            docs = query.stream()
            tickers: List[str] = []
            for doc in docs:
                data = doc.to_dict() or {}
                ticker = data.get("ticker")
                if ticker:
                    tickers.append(ticker)

            return tickers
        except Exception as e:
            print(f"Failed to get stale active markets: {e}")
            return []

    def get_markets_by_event(self, event_ticker: str) -> List[Market]:
        """Get all markets for a specific event.

        Args:
            event_ticker: Event ticker to filter by

        Returns:
            List of Market objects
        """
        try:
            db = self._get_db()
            markets_ref = db.collection("markets").where(
                "event_ticker", "==", event_ticker
            )
            markets_docs = markets_ref.stream()

            markets = []
            for doc in markets_docs:
                market = self._dict_to_market(doc.to_dict())
                if market:
                    markets.append(market)

            return markets
        except Exception as e:
            print(f"Failed to get markets by event {event_ticker}: {e}")
            return []

    def _dict_to_market(self, data: Dict[str, Any]) -> Optional[Market]:
        """Convert Firestore document dictionary to Market object.

        Args:
            data: Firestore document data

        Returns:
            Market object or None if conversion fails
        """
        try:
            # Convert timestamp fields back to datetime
            open_time = data["open_time"]
            if hasattr(open_time, "timestamp"):
                open_time = datetime.fromtimestamp(open_time.timestamp())
            elif isinstance(open_time, str):
                open_time = datetime.fromisoformat(open_time.replace("Z", "+00:00"))

            close_time = data["close_time"]
            if hasattr(close_time, "timestamp"):
                close_time = datetime.fromtimestamp(close_time.timestamp())
            elif isinstance(close_time, str):
                close_time = datetime.fromisoformat(close_time.replace("Z", "+00:00"))

            expiration_time = data["expiration_time"]
            if hasattr(expiration_time, "timestamp"):
                expiration_time = datetime.fromtimestamp(expiration_time.timestamp())
            elif isinstance(expiration_time, str):
                expiration_time = datetime.fromisoformat(
                    expiration_time.replace("Z", "+00:00")
                )

            latest_expiration_time = data["latest_expiration_time"]
            if hasattr(latest_expiration_time, "timestamp"):
                latest_expiration_time = datetime.fromtimestamp(
                    latest_expiration_time.timestamp()
                )
            elif isinstance(latest_expiration_time, str):
                latest_expiration_time = datetime.fromisoformat(
                    latest_expiration_time.replace("Z", "+00:00")
                )

            # Convert updated_at timestamp if present
            updated_at = None
            if "updated_at" in data and data["updated_at"] is not None:
                updated_at_value = data["updated_at"]
                if hasattr(updated_at_value, "timestamp"):
                    updated_at = datetime.fromtimestamp(updated_at_value.timestamp())
                elif isinstance(updated_at_value, str):
                    updated_at = datetime.fromisoformat(
                        updated_at_value.replace("Z", "+00:00")
                    )

            return Market(
                ticker=data["ticker"],
                event_ticker=data["event_ticker"],
                market_type=data["market_type"],
                title=data["title"],
                subtitle=data["subtitle"],
                yes_sub_title=data["yes_sub_title"],
                no_sub_title=data["no_sub_title"],
                open_time=open_time,
                close_time=close_time,
                expiration_time=expiration_time,
                latest_expiration_time=latest_expiration_time,
                settlement_timer_seconds=data["settlement_timer_seconds"],
                status=data["status"],
                response_price_units=data["response_price_units"],
                notional_value=data["notional_value"],
                notional_value_dollars=data["notional_value_dollars"],
                tick_size=data["tick_size"],
                yes_bid=data["yes_bid"],
                yes_bid_dollars=data["yes_bid_dollars"],
                yes_ask=data["yes_ask"],
                yes_ask_dollars=data["yes_ask_dollars"],
                no_bid=data["no_bid"],
                no_bid_dollars=data["no_bid_dollars"],
                no_ask=data["no_ask"],
                no_ask_dollars=data["no_ask_dollars"],
                last_price=data["last_price"],
                last_price_dollars=data["last_price_dollars"],
                previous_yes_bid=data["previous_yes_bid"],
                previous_yes_bid_dollars=data["previous_yes_bid_dollars"],
                previous_yes_ask=data["previous_yes_ask"],
                previous_yes_ask_dollars=data["previous_yes_ask_dollars"],
                previous_price=data["previous_price"],
                previous_price_dollars=data["previous_price_dollars"],
                volume=data["volume"],
                volume_24h=data["volume_24h"],
                liquidity=data["liquidity"],
                liquidity_dollars=data["liquidity_dollars"],
                open_interest=data["open_interest"],
                result=data["result"],
                can_close_early=data["can_close_early"],
                expiration_value=data["expiration_value"],
                category=data["category"],
                risk_limit_cents=data["risk_limit_cents"],
                rules_primary=data["rules_primary"],
                rules_secondary=data["rules_secondary"],
                settlement_value=data.get("settlement_value"),
                settlement_value_dollars=data.get("settlement_value_dollars"),
                price_level_structure=data.get("price_level_structure"),
                price_ranges=data.get("price_ranges"),
                updated_at=updated_at,
            )
        except Exception as e:
            print(f"Failed to convert dict to market: {e}")
            return None

    def get_all_markets(self) -> List[Market]:
        """Get all markets from the collection.

        Returns:
            List of Market objects
        """
        try:
            db = self._get_db()
            markets_ref = db.collection("markets")
            markets_docs = markets_ref.stream()

            markets = []
            for doc in markets_docs:
                market = self._dict_to_market(doc.to_dict())
                if market:
                    markets.append(market)

            return markets
        except Exception as e:
            print(f"Failed to get all markets: {e}")
            return []

    def count_markets(self) -> int:
        """Count all markets in the collection.

        Returns:
            Number of markets
        """
        try:
            db = self._get_db()
            markets_ref = db.collection("markets")
            # Use count aggregation for efficiency
            count_query = markets_ref.count()
            count_result = count_query.get()
            # Extract count value from aggregation result
            count_value = count_result[0][0].value
            return int(count_value) if count_value is not None else 0
        except Exception as e:
            print(f"Failed to count markets: {e}")
            # Fallback to streaming and counting
            try:
                markets_ref = db.collection("markets")
                count = sum(1 for _ in markets_ref.stream())
                return count
            except Exception as fallback_error:
                print(f"Fallback count also failed: {fallback_error}")
                return 0

    async def clear_all_markets(self) -> bool:
        """Clear all markets from the collection using BulkWriter.

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self._get_db()
            markets_ref = db.collection("markets")

            # Use BulkWriter for efficient bulk deletes
            bulk_writer = db.bulk_writer()
            deleted_count = 0

            print("   Fetching market documents to delete...")
            sys.stdout.flush()

            # Stream all documents and delete them
            for doc in markets_ref.stream():
                bulk_writer.delete(doc.reference)
                deleted_count += 1

                # Print progress every 1000 documents
                if deleted_count % 1000 == 0:
                    print(f"   Queued {deleted_count} documents for deletion...")
                    sys.stdout.flush()

            # Flush all pending operations
            print(f"   Flushing {deleted_count} delete operations...")
            sys.stdout.flush()
            bulk_writer.close()

            print(f"✅ Cleared {deleted_count} market documents")
            sys.stdout.flush()
            return True

        except Exception as e:
            print(f"❌ Error clearing markets: {e}")
            sys.stdout.flush()
            return False

    def close(self):
        """Close Firebase connections."""
        # if self._app:
        #     firebase_admin.delete_app(self._app)
        #     self._app = None
        self._db = None

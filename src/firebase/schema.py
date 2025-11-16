"""Firebase schema management for market data persistence."""

from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client


class FirebaseSchemaManager:
    """Manages Firebase schema definitions and DDL deployment."""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """Initialize Firebase schema manager.

        Args:
            project_id: Firebase project ID
            credentials_path: Path to service account credentials JSON file
        """
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

    def get_schema_definition(self) -> Dict[str, Any]:
        """Get the Firestore schema definition for all collections.

        Returns:
            Dictionary containing the schema definition
        """
        return {
            "collections": {
                "engine_events": {
                    "description": (
                        "Engine events collection tracking key system events"
                    ),
                    "fields": {
                        "event_id": {
                            "type": "string",
                            "description": "Unique event identifier (primary key)",
                            "required": True,
                            "indexed": True,
                        },
                        "timestamp": {
                            "type": "timestamp",
                            "description": "Event occurrence timestamp",
                            "required": True,
                            "indexed": True,
                        },
                        "event_name": {
                            "type": "string",
                            "description": "Name/type of the event",
                            "required": True,
                            "indexed": True,
                        },
                        "event_metadata": {
                            "type": "map",
                            "description": "JSON metadata for the event",
                            "required": False,
                        },
                    },
                },
                "markets": {
                    "description": (
                        "Market data collection for Kalshi prediction markets"
                    ),
                    "fields": {
                        "ticker": {
                            "type": "string",
                            "description": "Unique market identifier (primary key)",
                            "required": True,
                            "indexed": True,
                        },
                        "event_ticker": {
                            "type": "string",
                            "description": "Event identifier this market belongs to",
                            "required": True,
                            "indexed": True,
                        },
                        "market_type": {
                            "type": "string",
                            "description": "Type of market (binary, multi-way, etc.)",
                            "required": True,
                        },
                        "title": {
                            "type": "string",
                            "description": "Market title",
                            "required": True,
                        },
                        "subtitle": {
                            "type": "string",
                            "description": "Market subtitle",
                            "required": False,
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "Market status (open, closed, settled, etc.)"
                            ),
                            "required": True,
                            "indexed": True,
                        },
                        "last_price": {
                            "type": "number",
                            "description": "Last traded price in cents",
                            "required": False,
                        },
                        "last_price_dollars": {
                            "type": "string",
                            "description": "Last traded price in dollars",
                            "required": False,
                        },
                        "volume": {
                            "type": "number",
                            "description": "Trading volume",
                            "required": False,
                        },
                        "liquidity": {
                            "type": "number",
                            "description": "Market liquidity",
                            "required": False,
                        },
                        "open_time": {
                            "type": "timestamp",
                            "description": "Market open time",
                            "required": True,
                            "indexed": True,
                        },
                        "close_time": {
                            "type": "timestamp",
                            "description": "Market close time",
                            "required": True,
                            "indexed": True,
                        },
                        "expiration_time": {
                            "type": "timestamp",
                            "description": "Market expiration time",
                            "required": True,
                            "indexed": True,
                        },
                        "created_at": {
                            "type": "timestamp",
                            "description": "Record creation timestamp",
                            "required": True,
                            "indexed": True,
                        },
                        "updated_at": {
                            "type": "timestamp",
                            "description": "Record last update timestamp",
                            "required": True,
                            "indexed": True,
                        },
                        "crawled_at": {
                            "type": "timestamp",
                            "description": "Last crawl timestamp",
                            "required": True,
                            "indexed": True,
                        },
                        "data_hash": {
                            "type": "string",
                            "description": "Hash of market data for change detection",
                            "required": True,
                            "indexed": True,
                        },
                        "score": {
                            "type": "number",
                            "description": (
                                "Calculated score from market data "
                                "(original calculation)"
                            ),
                            "required": False,
                            "indexed": True,
                        },
                        "taker_potential": {
                            "type": "number",
                            "description": (
                                "Taker potential calculated from market data "
                                "(original)"
                            ),
                            "required": False,
                            "indexed": True,
                        },
                        "maker_potential": {
                            "type": "number",
                            "description": (
                                "Maker potential calculated from market data "
                                "(original)"
                            ),
                            "required": False,
                            "indexed": True,
                        },
                        "score_orderbook": {
                            "type": "number",
                            "description": (
                                "Calculated score from orderbook data " "(deep scan)"
                            ),
                            "required": False,
                            "indexed": True,
                        },
                        "taker_potential_orderbook": {
                            "type": "number",
                            "description": (
                                "Taker potential calculated from orderbook data "
                                "(deep scan)"
                            ),
                            "required": False,
                            "indexed": True,
                        },
                        "maker_potential_orderbook": {
                            "type": "number",
                            "description": (
                                "Maker potential calculated from orderbook data "
                                "(deep scan)"
                            ),
                            "required": False,
                            "indexed": True,
                        },
                    },
                },
                "orderbooks": {
                    "description": (
                        "Orderbook data collection for Kalshi prediction markets"
                    ),
                    "fields": {
                        "ticker": {
                            "type": "string",
                            "description": (
                                "Market ticker this orderbook belongs to (primary key)"
                            ),
                            "required": True,
                            "indexed": True,
                        },
                        "yes": {
                            "type": "array",
                            "description": "List of yes bid price levels",
                            "required": True,
                        },
                        "no": {
                            "type": "array",
                            "description": "List of no bid price levels",
                            "required": True,
                        },
                        "yes_dollars": {
                            "type": "array",
                            "description": "List of yes bid price levels in dollars",
                            "required": True,
                        },
                        "no_dollars": {
                            "type": "array",
                            "description": "List of no bid price levels in dollars",
                            "required": True,
                        },
                        "best_yes_bid": {
                            "type": "number",
                            "description": "Best yes bid price in cents",
                            "required": False,
                        },
                        "best_yes_bid_qty": {
                            "type": "number",
                            "description": "Quantity of best yes bid",
                            "required": False,
                        },
                        "best_no_bid": {
                            "type": "number",
                            "description": "Best no bid price in cents",
                            "required": False,
                        },
                        "best_no_bid_qty": {
                            "type": "number",
                            "description": "Quantity of best no bid",
                            "required": False,
                        },
                        "yes_ask_l1": {
                            "type": "number",
                            "description": "Yes ask at level 1 in cents",
                            "required": False,
                        },
                        "yes_ask_l1_qty": {
                            "type": "number",
                            "description": "Quantity of yes ask at level 1",
                            "required": False,
                        },
                        "spread": {
                            "type": "number",
                            "description": "Spread between yes ask L1 and best yes bid",
                            "required": False,
                        },
                        "mid": {
                            "type": "number",
                            "description": "Midpoint price in cents",
                            "required": False,
                        },
                        "bid_depth": {
                            "type": "number",
                            "description": "YES-side bid depth",
                            "required": False,
                        },
                        "ask_depth": {
                            "type": "number",
                            "description": "YES-side ask depth",
                            "required": False,
                        },
                        "obi": {
                            "type": "number",
                            "description": "Orderbook imbalance",
                            "required": False,
                        },
                        "micro": {
                            "type": "number",
                            "description": "Micro price in cents",
                            "required": False,
                        },
                        "micro_tilt": {
                            "type": "number",
                            "description": "Micro tilt in cents",
                            "required": False,
                        },
                        "score": {
                            "type": "number",
                            "description": "Calculated score for this orderbook",
                            "required": True,
                            "indexed": True,
                        },
                        "taker_potential": {
                            "type": "number",
                            "description": "Calculated taker potential",
                            "required": True,
                            "indexed": True,
                        },
                        "maker_potential": {
                            "type": "number",
                            "description": "Calculated maker potential",
                            "required": True,
                            "indexed": True,
                        },
                        "created_at": {
                            "type": "timestamp",
                            "description": "Record creation timestamp",
                            "required": True,
                            "indexed": True,
                        },
                        "updated_at": {
                            "type": "timestamp",
                            "description": "Record last update timestamp",
                            "required": True,
                            "indexed": True,
                        },
                    },
                },
            }
        }

    def deploy_schema(self) -> bool:
        """Deploy schema to Firestore (create collections and indexes).

        Note: Firestore is schemaless, so this creates the collection
        structure and documents the schema for reference.

        Returns:
            True if deployment successful, False otherwise
        """
        try:
            db = self._get_db()
            schema = self.get_schema_definition()

            # Deploy markets collection
            markets_schema_ref = db.collection("_schema").document("markets")
            markets_schema_ref.set(
                {
                    "version": "1.0.0",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                    "definition": schema["collections"]["markets"],
                }
            )

            # Deploy orderbooks collection
            orderbooks_schema_ref = db.collection("_schema").document("orderbooks")
            orderbooks_schema_ref.set(
                {
                    "version": "1.0.0",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                    "definition": schema["collections"]["orderbooks"],
                }
            )

            # Create a sample document to ensure markets collection exists
            markets_ref = db.collection("markets")
            markets_sample = markets_ref.document("_schema_init")
            markets_sample.set(
                {
                    "ticker": "_schema_init",
                    "event_ticker": "SYSTEM",
                    "market_type": "system",
                    "title": "Schema Initialization",
                    "status": "closed",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                    "crawled_at": firestore.SERVER_TIMESTAMP,
                    "data_hash": "schema_init",
                }
            )
            markets_sample.delete()

            # Create a sample document to ensure orderbooks collection exists
            orderbooks_ref = db.collection("orderbooks")
            orderbooks_sample = orderbooks_ref.document("_schema_init")
            orderbooks_sample.set(
                {
                    "ticker": "_schema_init",
                    "yes": [],
                    "no": [],
                    "yes_dollars": [],
                    "no_dollars": [],
                    "score": 0.0,
                    "taker_potential": 0.0,
                    "maker_potential": 0.0,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )
            orderbooks_sample.delete()

            # Deploy engine_events collection
            events_schema_ref = db.collection("_schema").document("engine_events")
            events_schema_ref.set(
                {
                    "version": "1.0.0",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                    "definition": schema["collections"]["engine_events"],
                }
            )

            # Create a sample document to ensure engine_events collection exists
            events_ref = db.collection("engine_events")
            events_sample = events_ref.document("_schema_init")
            events_sample.set(
                {
                    "event_id": "_schema_init",
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "event_name": "schema_initialization",
                    "event_metadata": {},
                }
            )
            events_sample.delete()

            print("Schema deployment successful")
            return True

        except Exception as e:
            print(f"Schema deployment failed: {e}")
            return False

    def validate_schema(self) -> bool:
        """Validate that the current schema matches the expected definition.

        Returns:
            True if schema is valid, False otherwise
        """
        try:
            db = self._get_db()
            schema_ref = db.collection("_schema").document("markets")
            schema_doc = schema_ref.get()

            if not schema_doc.exists:
                return False

            current_schema = schema_doc.to_dict()

            # Compare schema versions and definitions
            return (
                current_schema.get("version") == "1.0.0"
                and "definition" in current_schema
            )

        except Exception as e:
            print(f"Schema validation failed: {e}")
            return False

    def get_schema_version(self) -> Optional[str]:
        """Get the current schema version.

        Returns:
            Schema version string or None if not found
        """
        try:
            db = self._get_db()
            schema_ref = db.collection("_schema").document("markets")
            schema_doc = schema_ref.get()

            if schema_doc.exists:
                doc_dict = schema_doc.to_dict()
                if doc_dict:
                    return str(doc_dict.get("version", ""))
                return None

            return None

        except Exception as e:
            print(f"Failed to get schema version: {e}")
            return None

    def close(self):
        """Close Firebase connections."""
        if self._app:
            firebase_admin.delete_app(self._app)
            self._app = None
        self._db = None

"""Orderbook Data Access Object for Firebase Firestore operations."""

from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client

# Import Orderbook - handle both direct and relative imports
try:
    from src.kalshi.service import Orderbook
except ImportError:
    from kalshi.service import Orderbook  # type: ignore[no-redef]


class OrderbookDAO:
    """Data Access Object for Orderbook data in Firebase Firestore."""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """Initialize Orderbook DAO.

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

    def _orderbook_to_dict(
        self,
        orderbook: Orderbook,
        ticker: str,
        score: float,
        taker_potential: float,
        maker_potential: float,
    ) -> Dict[str, Any]:
        """Convert Orderbook object to Firestore document dictionary.

        Args:
            orderbook: Orderbook object to convert
            ticker: Market ticker this orderbook belongs to
            score: Calculated score for this orderbook
            taker_potential: Calculated taker potential
            maker_potential: Calculated maker potential

        Returns:
            Dictionary representation for Firestore
        """
        now = firestore.SERVER_TIMESTAMP

        # Convert OrderbookLevel objects to dicts
        yes_levels = [
            {"price": level.price, "count": level.count} for level in orderbook.yes
        ]
        no_levels = [
            {"price": level.price, "count": level.count} for level in orderbook.no
        ]

        # Convert yes_dollars and no_dollars tuples to lists
        yes_dollars_list = [
            {"price": price, "count": count} for price, count in orderbook.yes_dollars
        ]
        no_dollars_list = [
            {"price": price, "count": count} for price, count in orderbook.no_dollars
        ]

        # Calculate orderbook properties
        best_yes_bid = orderbook.best_yes_bid
        best_yes_bid_qty = orderbook.best_yes_bid_qty
        best_no_bid = orderbook.best_no_bid
        best_no_bid_qty = orderbook.best_no_bid_qty
        yes_ask_l1 = orderbook.yes_ask_l1
        yes_ask_l1_qty = orderbook.yes_ask_l1_qty
        spread = orderbook.spread
        mid = orderbook.mid
        bid_depth = orderbook.bid_depth
        ask_depth = orderbook.ask_depth
        obi = orderbook.obi
        micro = orderbook.micro
        micro_tilt = orderbook.micro_tilt

        return {
            "ticker": ticker,
            "yes": yes_levels,
            "no": no_levels,
            "yes_dollars": yes_dollars_list,
            "no_dollars": no_dollars_list,
            # Calculated properties
            "best_yes_bid": best_yes_bid,
            "best_yes_bid_qty": best_yes_bid_qty,
            "best_no_bid": best_no_bid,
            "best_no_bid_qty": best_no_bid_qty,
            "yes_ask_l1": yes_ask_l1,
            "yes_ask_l1_qty": yes_ask_l1_qty,
            "spread": spread,
            "mid": mid,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "obi": obi,
            "micro": micro,
            "micro_tilt": micro_tilt,
            # Score properties
            "score": score,
            "taker_potential": taker_potential,
            "maker_potential": maker_potential,
            # Timestamps
            "created_at": now,
            "updated_at": now,
        }

    def create_orderbook(
        self,
        orderbook: Orderbook,
        ticker: str,
        score: float,
        taker_potential: float,
        maker_potential: float,
    ) -> bool:
        """Create a new orderbook in Firestore.

        Args:
            orderbook: Orderbook object to create
            ticker: Market ticker this orderbook belongs to
            score: Calculated score for this orderbook
            taker_potential: Calculated taker potential
            maker_potential: Calculated maker potential

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self._get_db()
            # Use ticker as document ID to store latest orderbook per market
            orderbook_ref = db.collection("orderbooks").document(ticker)
            orderbook_data = self._orderbook_to_dict(
                orderbook, ticker, score, taker_potential, maker_potential
            )
            orderbook_ref.set(orderbook_data)
            return True
        except Exception as e:
            print(f"Failed to create orderbook for {ticker}: {e}")
            return False

    def update_orderbook(
        self,
        orderbook: Orderbook,
        ticker: str,
        score: float,
        taker_potential: float,
        maker_potential: float,
    ) -> bool:
        """Update an existing orderbook in Firestore.

        Args:
            orderbook: Orderbook object to update
            ticker: Market ticker this orderbook belongs to
            score: Calculated score for this orderbook
            taker_potential: Calculated taker potential
            maker_potential: Calculated maker potential

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self._get_db()
            orderbook_ref = db.collection("orderbooks").document(ticker)
            orderbook_data = self._orderbook_to_dict(
                orderbook, ticker, score, taker_potential, maker_potential
            )
            # Remove created_at when updating (keep original creation time)
            orderbook_data.pop("created_at", None)
            orderbook_ref.update(orderbook_data)
            return True
        except Exception as e:
            print(f"Failed to update orderbook for {ticker}: {e}")
            return False

    def upsert_orderbook(
        self,
        orderbook: Orderbook,
        ticker: str,
        score: float,
        taker_potential: float,
        maker_potential: float,
    ) -> bool:
        """Create or update an orderbook in Firestore.

        Args:
            orderbook: Orderbook object to upsert
            ticker: Market ticker this orderbook belongs to
            score: Calculated score for this orderbook
            taker_potential: Calculated taker potential
            maker_potential: Calculated maker potential

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self._get_db()
            orderbook_ref = db.collection("orderbooks").document(ticker)
            orderbook_data = self._orderbook_to_dict(
                orderbook, ticker, score, taker_potential, maker_potential
            )
            orderbook_ref.set(orderbook_data, merge=True)
            return True
        except Exception as e:
            print(f"Failed to upsert orderbook for {ticker}: {e}")
            return False

    def get_orderbook(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get an orderbook by ticker.

        Args:
            ticker: Market ticker

        Returns:
            Orderbook document dictionary or None if not found
        """
        try:
            db = self._get_db()
            orderbook_ref = db.collection("orderbooks").document(ticker)
            doc = orderbook_ref.get()
            if doc.exists:
                result = doc.to_dict()
                if result is not None:
                    return dict(result)
            return None
        except Exception as e:
            print(f"Failed to get orderbook for {ticker}: {e}")
            return None

    def close(self) -> None:
        """Close the DAO and cleanup resources."""
        # Firestore client doesn't need explicit cleanup
        self._db = None
        self._app = None

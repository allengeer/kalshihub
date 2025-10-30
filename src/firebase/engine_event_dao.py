"""Data Access Object for engine events in Firebase."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client

from .engine_event import EngineEvent


class EngineEventDAO:
    """Data Access Object for engine events in Firebase Firestore."""

    COLLECTION_NAME = "engine_events"

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """Initialize EngineEvent DAO.

        Args:
            project_id: Firebase project ID
            credentials_path: Optional path to service account credentials JSON file
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self._db: Optional[Client] = None
        self._app: Optional[firebase_admin.App] = None

    def _get_db(self) -> Client:
        """Get or create Firestore client.

        Returns:
            Firestore client instance
        """
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

    def create_event(
        self,
        event_name: str,
        event_metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> EngineEvent:
        """Create a new engine event.

        Args:
            event_name: Name/type of the event
            event_metadata: Optional metadata dictionary
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Created EngineEvent
        """
        db = self._get_db()

        # Generate event ID
        event_id = str(uuid.uuid4())

        # Use current time if not provided
        if timestamp is None:
            timestamp = datetime.now()

        # Create event object
        event = EngineEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_name=event_name,
            event_metadata=event_metadata or {},
        )

        # Store in Firestore
        doc_ref = db.collection(self.COLLECTION_NAME).document(event_id)
        doc_ref.set(event.to_dict())

        return event

    def get_event(self, event_id: str) -> Optional[EngineEvent]:
        """Get an event by ID.

        Args:
            event_id: Event ID to retrieve

        Returns:
            EngineEvent if found, None otherwise
        """
        db = self._get_db()
        doc_ref = db.collection(self.COLLECTION_NAME).document(event_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        doc_dict = doc.to_dict()
        if doc_dict is None:
            return None

        return EngineEvent.from_dict(doc_dict)

    def get_events_by_name(
        self, event_name: str, limit: Optional[int] = None
    ) -> List[EngineEvent]:
        """Get events by event name.

        Args:
            event_name: Event name to filter by
            limit: Optional limit on number of results

        Returns:
            List of EngineEvents matching the name
        """
        db = self._get_db()
        query = db.collection(self.COLLECTION_NAME).where(
            "event_name", "==", event_name
        )

        if limit:
            query = query.limit(limit)

        docs = query.order_by(
            "timestamp", direction=firestore.Query.DESCENDING
        ).stream()

        events = []
        for doc in docs:
            doc_dict = doc.to_dict()
            if doc_dict:
                events.append(EngineEvent.from_dict(doc_dict))

        return events

    def get_recent_events(self, limit: int = 100) -> List[EngineEvent]:
        """Get most recent events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent EngineEvents
        """
        db = self._get_db()
        query = (
            db.collection(self.COLLECTION_NAME)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )

        docs = query.stream()

        events = []
        for doc in docs:
            doc_dict = doc.to_dict()
            if doc_dict:
                events.append(EngineEvent.from_dict(doc_dict))

        return events

    def get_events_in_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[EngineEvent]:
        """Get events within a time range.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            List of EngineEvents in the time range
        """
        db = self._get_db()
        query = (
            db.collection(self.COLLECTION_NAME)
            .where("timestamp", ">=", start_time)
            .where("timestamp", "<=", end_time)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
        )

        docs = query.stream()

        events = []
        for doc in docs:
            doc_dict = doc.to_dict()
            if doc_dict:
                events.append(EngineEvent.from_dict(doc_dict))

        return events

    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID.

        Args:
            event_id: Event ID to delete

        Returns:
            True if deleted, False if not found
        """
        db = self._get_db()
        doc_ref = db.collection(self.COLLECTION_NAME).document(event_id)

        doc = doc_ref.get()
        if not doc.exists:
            return False

        doc_ref.delete()
        return True

    def delete_old_events(self, before_time: datetime) -> int:
        """Delete events older than a specified time.

        Args:
            before_time: Delete events before this time

        Returns:
            Number of events deleted
        """
        db = self._get_db()
        query = db.collection(self.COLLECTION_NAME).where("timestamp", "<", before_time)

        docs = query.stream()

        batch = db.batch()
        count = 0

        for doc in docs:
            batch.delete(doc.reference)
            count += 1

            # Commit in batches of 500 (Firestore limit)
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()

        # Commit remaining
        if count % 500 != 0:
            batch.commit()

        return count

    def close(self):
        """Close Firebase connections."""
        if self._app:
            firebase_admin.delete_app(self._app)
            self._app = None
        self._db = None

"""Tests for EngineEventDAO."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from src.firebase.engine_event_dao import EngineEventDAO


class TestEngineEventDAO:
    """Test cases for EngineEventDAO."""

    def test_initialization(self):
        """Test DAO initialization."""
        dao = EngineEventDAO(project_id="test-project")
        assert dao.project_id == "test-project"
        assert dao.credentials_path is None

    def test_initialization_with_credentials(self):
        """Test DAO initialization with credentials path."""
        dao = EngineEventDAO(
            project_id="test-project", credentials_path="/path/to/creds.json"
        )
        assert dao.project_id == "test-project"
        assert dao.credentials_path == "/path/to/creds.json"

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_create_event(self, mock_firestore, mock_firebase_admin):
        """Test creating an event."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        dao = EngineEventDAO(project_id="test-project")

        # Create event
        event = dao.create_event(
            event_name="test_event",
            event_metadata={"key": "value"},
        )

        assert event.event_name == "test_event"
        assert event.event_metadata == {"key": "value"}
        assert isinstance(event.timestamp, datetime)
        assert event.event_id is not None

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_get_event(self, mock_firestore, mock_firebase_admin):
        """Test getting an event by ID."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "event_id": "test-id",
            "timestamp": datetime.now(),
            "event_name": "test_event",
            "event_metadata": {},
        }
        mock_db.collection().document().get.return_value = mock_doc

        dao = EngineEventDAO(project_id="test-project")
        event = dao.get_event("test-id")

        assert event is not None
        assert event.event_id == "test-id"

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_get_event_not_found(self, mock_firestore, mock_firebase_admin):
        """Test getting a non-existent event."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection().document().get.return_value = mock_doc

        dao = EngineEventDAO(project_id="test-project")
        event = dao.get_event("nonexistent-id")

        assert event is None

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_get_recent_events(self, mock_firestore, mock_firebase_admin):
        """Test getting recent events."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "event_id": "test-id",
            "timestamp": datetime.now(),
            "event_name": "test_event",
            "event_metadata": {},
        }
        mock_db.collection().order_by().limit().stream.return_value = [mock_doc]

        dao = EngineEventDAO(project_id="test-project")
        events = dao.get_recent_events(limit=10)

        assert len(events) == 1
        assert events[0].event_id == "test-id"

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_delete_event(self, mock_firestore, mock_firebase_admin):
        """Test deleting an event."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_doc = Mock()
        mock_doc.exists = True
        mock_db.collection().document().get.return_value = mock_doc

        dao = EngineEventDAO(project_id="test-project")
        result = dao.delete_event("test-id")

        assert result is True

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_get_events_by_name(self, mock_firestore, mock_firebase_admin):
        """Test getting events by name."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_doc1 = Mock()
        mock_doc1.to_dict.return_value = {
            "event_id": "test-id-1",
            "timestamp": datetime.now(),
            "event_name": "test_event",
            "event_metadata": {},
        }
        mock_doc2 = Mock()
        mock_doc2.to_dict.return_value = {
            "event_id": "test-id-2",
            "timestamp": datetime.now(),
            "event_name": "test_event",
            "event_metadata": {},
        }
        mock_db.collection().where().limit().order_by().stream.return_value = [
            mock_doc1,
            mock_doc2,
        ]

        dao = EngineEventDAO(project_id="test-project")
        events = dao.get_events_by_name("test_event", limit=10)

        assert len(events) == 2
        assert events[0].event_id == "test-id-1"
        assert events[1].event_id == "test-id-2"

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_get_events_by_name_no_limit(self, mock_firestore, mock_firebase_admin):
        """Test getting events by name without limit."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "event_id": "test-id",
            "timestamp": datetime.now(),
            "event_name": "test_event",
            "event_metadata": {},
        }
        mock_db.collection().where().order_by().stream.return_value = [mock_doc]

        dao = EngineEventDAO(project_id="test-project")
        events = dao.get_events_by_name("test_event")

        assert len(events) == 1
        assert events[0].event_id == "test-id"

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_get_events_in_range(self, mock_firestore, mock_firebase_admin):
        """Test getting events in time range."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 12, 31)

        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "event_id": "test-id",
            "timestamp": datetime(2024, 6, 15),
            "event_name": "test_event",
            "event_metadata": {},
        }
        mock_db.collection().where().where().order_by().stream.return_value = [mock_doc]

        dao = EngineEventDAO(project_id="test-project")
        events = dao.get_events_in_range(start_time, end_time)

        assert len(events) == 1
        assert events[0].event_id == "test-id"

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_delete_event_not_found(self, mock_firestore, mock_firebase_admin):
        """Test deleting a non-existent event."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection().document().get.return_value = mock_doc

        dao = EngineEventDAO(project_id="test-project")
        result = dao.delete_event("nonexistent-id")

        assert result is False

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_delete_old_events(self, mock_firestore, mock_firebase_admin):
        """Test deleting old events."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_batch = MagicMock()
        mock_db.batch.return_value = mock_batch

        # Create 3 mock documents
        mock_docs = []
        for i in range(3):
            mock_doc = Mock()
            mock_doc.reference = Mock()
            mock_docs.append(mock_doc)

        mock_db.collection().where().stream.return_value = mock_docs

        dao = EngineEventDAO(project_id="test-project")
        before_time = datetime(2024, 1, 1)
        count = dao.delete_old_events(before_time)

        assert count == 3
        assert mock_batch.delete.call_count == 3
        assert mock_batch.commit.call_count == 1

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_delete_old_events_large_batch(self, mock_firestore, mock_firebase_admin):
        """Test deleting old events with batching."""
        # Setup mocks
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        mock_firebase_admin._apps = []

        mock_batch = MagicMock()
        mock_db.batch.return_value = mock_batch

        # Create 1000 mock documents to test batching
        mock_docs = []
        for i in range(1000):
            mock_doc = Mock()
            mock_doc.reference = Mock()
            mock_docs.append(mock_doc)

        mock_db.collection().where().stream.return_value = mock_docs

        dao = EngineEventDAO(project_id="test-project")
        before_time = datetime(2024, 1, 1)
        count = dao.delete_old_events(before_time)

        assert count == 1000
        # Should commit twice: once at 500, once at end
        assert mock_batch.commit.call_count == 2

    @patch("src.firebase.engine_event_dao.firebase_admin")
    @patch("src.firebase.engine_event_dao.firestore")
    def test_close(self, mock_firestore, mock_firebase_admin):
        """Test closing DAO connections."""
        mock_app = Mock()
        mock_firebase_admin._apps = []

        dao = EngineEventDAO(project_id="test-project")
        dao._app = mock_app

        dao.close()

        assert dao._app is None
        assert dao._db is None

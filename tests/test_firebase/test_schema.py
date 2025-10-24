"""Tests for Firebase schema management."""

from unittest.mock import MagicMock, patch

import pytest

from src.firebase.schema import FirebaseSchemaManager


class TestFirebaseSchemaManager:
    """Test cases for FirebaseSchemaManager."""

    @pytest.fixture
    def schema_manager(self):
        """Create a FirebaseSchemaManager instance for testing."""
        manager = FirebaseSchemaManager(
            project_id="test-project",
            credentials_path=None,  # Don't try to load credentials
        )
        # Pre-mock the _db to avoid Firebase initialization
        manager._db = MagicMock()
        return manager

    def test_initialization(self, schema_manager):
        """Test schema manager initialization."""
        assert schema_manager.project_id == "test-project"
        assert schema_manager.credentials_path is None
        # _db and _app are mocked for testing
        assert schema_manager._app is None

    def test_get_schema_definition(self, schema_manager):
        """Test schema definition retrieval."""
        schema = schema_manager.get_schema_definition()

        assert "collections" in schema
        assert "markets" in schema["collections"]

        markets_schema = schema["collections"]["markets"]
        assert "fields" in markets_schema
        assert "ticker" in markets_schema["fields"]
        assert markets_schema["fields"]["ticker"]["type"] == "string"
        assert markets_schema["fields"]["ticker"]["required"] is True
        assert markets_schema["fields"]["ticker"]["indexed"] is True

    def test_deploy_schema_success(self, schema_manager):
        """Test successful schema deployment."""
        # Mock the database operations
        mock_collection = MagicMock()
        mock_doc = MagicMock()
        mock_collection.document.return_value = mock_doc
        schema_manager._db.collection.return_value = mock_collection

        result = schema_manager.deploy_schema()

        assert result is True
        # Should be called for both _schema and markets collections
        assert schema_manager._db.collection.call_count >= 2
        # Check that set was called (for both schema and init document)
        assert mock_doc.set.call_count >= 2

    def test_deploy_schema_failure(self, schema_manager):
        """Test schema deployment failure."""
        # Mock the database to raise an exception
        schema_manager._db.collection.side_effect = Exception("Firebase error")

        result = schema_manager.deploy_schema()

        assert result is False

    def test_validate_schema_success(self, schema_manager):
        """Test successful schema validation."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "version": "1.0.0",
            "definition": {"test": "schema"},
        }

        mock_collection = MagicMock()
        mock_schema_doc = MagicMock()
        mock_schema_doc.get.return_value = mock_doc
        mock_collection.document.return_value = mock_schema_doc
        schema_manager._db.collection.return_value = mock_collection

        result = schema_manager.validate_schema()

        assert result is True

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_validate_schema_not_found(
        self, mock_client, mock_init_app, schema_manager
    ):
        """Test schema validation when schema not found."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_client.return_value.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = schema_manager.validate_schema()

        assert result is False

    def test_get_schema_version_success(self, schema_manager):
        """Test successful schema version retrieval."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"version": "1.0.0"}

        mock_collection = MagicMock()
        mock_schema_doc = MagicMock()
        mock_schema_doc.get.return_value = mock_doc
        mock_collection.document.return_value = mock_schema_doc
        schema_manager._db.collection.return_value = mock_collection

        version = schema_manager.get_schema_version()

        assert version == "1.0.0"

    def test_get_schema_version_not_found(self, schema_manager):
        """Test schema version retrieval when schema not found."""
        mock_doc = MagicMock()
        mock_doc.exists = False

        mock_collection = MagicMock()
        mock_schema_doc = MagicMock()
        mock_schema_doc.get.return_value = mock_doc
        mock_collection.document.return_value = mock_schema_doc
        schema_manager._db.collection.return_value = mock_collection

        version = schema_manager.get_schema_version()

        assert version is None

    def test_close(self, schema_manager):
        """Test closing Firebase connections."""
        with patch("firebase_admin.delete_app") as mock_delete_app:
            mock_app = MagicMock()
            schema_manager._app = mock_app
            schema_manager.close()

            mock_delete_app.assert_called_once_with(mock_app)
            assert schema_manager._app is None
            assert schema_manager._db is None
            assert schema_manager._db is None

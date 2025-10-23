"""Tests for Firebase schema management."""

from unittest.mock import MagicMock, patch

import pytest

from src.firebase.schema import FirebaseSchemaManager


class TestFirebaseSchemaManager:
    """Test cases for FirebaseSchemaManager."""

    @pytest.fixture
    def schema_manager(self):
        """Create a FirebaseSchemaManager instance for testing."""
        return FirebaseSchemaManager(
            project_id="test-project", credentials_path="test-credentials.json"
        )

    def test_initialization(self, schema_manager):
        """Test schema manager initialization."""
        assert schema_manager.project_id == "test-project"
        assert schema_manager.credentials_path == "test-credentials.json"
        assert schema_manager._db is None
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

    @patch("firebase_admin.initialize_app")
    @patch("firestore.client")
    def test_deploy_schema_success(self, mock_client, mock_init_app, schema_manager):
        """Test successful schema deployment."""
        mock_client.return_value.collection.return_value.document.return_value.set.return_value = (
            None
        )
        mock_client.return_value.collection.return_value.document.return_value.delete.return_value = (
            None
        )

        result = schema_manager.deploy_schema()

        assert result is True
        mock_init_app.assert_called_once()
        mock_client.assert_called_once()

    @patch("firebase_admin.initialize_app")
    @patch("firestore.client")
    def test_deploy_schema_failure(self, mock_client, mock_init_app, schema_manager):
        """Test schema deployment failure."""
        mock_client.side_effect = Exception("Firebase error")

        result = schema_manager.deploy_schema()

        assert result is False

    @patch("firebase_admin.initialize_app")
    @patch("firestore.client")
    def test_validate_schema_success(self, mock_client, mock_init_app, schema_manager):
        """Test successful schema validation."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "version": "1.0.0",
            "definition": {"test": "schema"},
        }
        mock_client.return_value.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = schema_manager.validate_schema()

        assert result is True

    @patch("firebase_admin.initialize_app")
    @patch("firestore.client")
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

    @patch("firebase_admin.initialize_app")
    @patch("firestore.client")
    def test_get_schema_version_success(
        self, mock_client, mock_init_app, schema_manager
    ):
        """Test successful schema version retrieval."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"version": "1.0.0"}
        mock_client.return_value.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        version = schema_manager.get_schema_version()

        assert version == "1.0.0"

    @patch("firebase_admin.initialize_app")
    @patch("firestore.client")
    def test_get_schema_version_not_found(
        self, mock_client, mock_init_app, schema_manager
    ):
        """Test schema version retrieval when schema not found."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_client.return_value.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        version = schema_manager.get_schema_version()

        assert version is None

    def test_close(self, schema_manager):
        """Test closing Firebase connections."""
        with patch("firebase_admin.delete_app") as mock_delete_app:
            schema_manager._app = MagicMock()
            schema_manager.close()

            mock_delete_app.assert_called_once_with(schema_manager._app)
            assert schema_manager._app is None
            assert schema_manager._db is None
            assert schema_manager._db is None

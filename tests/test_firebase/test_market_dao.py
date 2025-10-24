"""Tests for Market DAO."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.firebase.market_dao import MarketDAO
from src.kalshi.service import Market


class TestMarketDAO:
    """Test cases for MarketDAO."""

    @pytest.fixture
    def market_dao(self):
        """Create a MarketDAO instance for testing."""
        dao = MarketDAO(
            project_id="test-project",
            credentials_path=None,  # Don't try to load credentials
        )
        # Pre-mock the _db to avoid Firebase initialization
        dao._db = MagicMock()
        return dao

    @pytest.fixture
    def sample_market(self):
        """Create a sample market for testing."""
        return Market(
            ticker="TEST-2024",
            event_ticker="EVENT-2024",
            market_type="binary",
            title="Test Market",
            subtitle="Test Subtitle",
            yes_sub_title="Yes",
            no_sub_title="No",
            open_time=datetime(2024, 1, 1),
            close_time=datetime(2024, 12, 31),
            expiration_time=datetime(2024, 12, 31),
            latest_expiration_time=datetime(2024, 12, 31),
            settlement_timer_seconds=3600,
            status="open",
            response_price_units="cents",
            notional_value=10000,
            notional_value_dollars="100.00",
            tick_size=1,
            yes_bid=45,
            yes_bid_dollars="0.45",
            yes_ask=55,
            yes_ask_dollars="0.55",
            no_bid=45,
            no_bid_dollars="0.45",
            no_ask=55,
            no_ask_dollars="0.55",
            last_price=50,
            last_price_dollars="0.50",
            previous_yes_bid=45,
            previous_yes_bid_dollars="0.45",
            previous_yes_ask=55,
            previous_yes_ask_dollars="0.55",
            previous_price=50,
            previous_price_dollars="0.50",
            volume=1000,
            volume_24h=500,
            liquidity=5000,
            liquidity_dollars="50.00",
            open_interest=100,
            result="",
            can_close_early=False,
            expiration_value="",
            category="politics",
            risk_limit_cents=100000,
            rules_primary="",
            rules_secondary="",
        )

    def test_initialization(self, market_dao):
        """Test DAO initialization."""
        assert market_dao.project_id == "test-project"
        assert market_dao.credentials_path is None  # Set to None in fixture for testing
        # _db is mocked in fixture, _app is None
        assert market_dao._app is None

    def test_calculate_data_hash(self, market_dao, sample_market):
        """Test data hash calculation."""
        hash1 = market_dao._calculate_data_hash(sample_market)
        hash2 = market_dao._calculate_data_hash(sample_market)

        # Same market should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length

        # Different market should produce different hash
        sample_market.title = "Different Title"
        hash3 = market_dao._calculate_data_hash(sample_market)
        assert hash1 != hash3

    def test_market_to_dict(self, market_dao, sample_market):
        """Test market to dictionary conversion."""
        market_dict = market_dao._market_to_dict(sample_market)

        assert market_dict["ticker"] == sample_market.ticker
        assert market_dict["title"] == sample_market.title
        assert market_dict["status"] == sample_market.status
        # SERVER_TIMESTAMP is a firestore sentinel value
        assert "created_at" in market_dict
        assert "updated_at" in market_dict
        assert "crawled_at" in market_dict
        assert "data_hash" in market_dict

    def test_create_market_success(self, market_dao, sample_market):
        """Test successful market creation."""
        # Mock the Firestore client
        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value.set.return_value = None

        with patch.object(market_dao, "_get_db", return_value=mock_db):
            result = market_dao.create_market(sample_market)

            assert result is True
            mock_db.collection.assert_called_once_with("markets")
            mock_db.collection.return_value.document.assert_called_once_with(
                sample_market.ticker
            )

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_create_market_failure(
        self, mock_client, mock_init_app, market_dao, sample_market
    ):
        """Test market creation failure."""
        market_dao._db.collection.side_effect = Exception("Firebase error")

        result = market_dao.create_market(sample_market)

        assert result is False

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_get_market_success(self, mock_client, mock_init_app, market_dao):
        """Test successful market retrieval."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "ticker": "TEST-2024",
            "event_ticker": "EVENT-2024",
            "market_type": "binary",
            "title": "Test Market",
            "subtitle": "Test Subtitle",
            "yes_sub_title": "Yes",
            "no_sub_title": "No",
            "status": "open",
            "open_time": datetime(2024, 1, 1),
            "close_time": datetime(2024, 12, 31),
            "expiration_time": datetime(2024, 12, 31),
            "latest_expiration_time": datetime(2024, 12, 31),
            "settlement_timer_seconds": 3600,
            "response_price_units": "cents",
            "notional_value": 10000,
            "notional_value_dollars": "100.00",
            "tick_size": 1,
            "yes_bid": 45,
            "yes_bid_dollars": "0.45",
            "yes_ask": 55,
            "yes_ask_dollars": "0.55",
            "no_bid": 45,
            "no_bid_dollars": "0.45",
            "no_ask": 55,
            "no_ask_dollars": "0.55",
            "last_price": 50,
            "last_price_dollars": "0.50",
            "previous_yes_bid": 45,
            "previous_yes_bid_dollars": "0.45",
            "previous_yes_ask": 55,
            "previous_yes_ask_dollars": "0.55",
            "previous_price": 50,
            "previous_price_dollars": "0.50",
            "volume": 1000,
            "volume_24h": 500,
            "liquidity": 5000,
            "liquidity_dollars": "50.00",
            "open_interest": 100,
            "result": "",
            "can_close_early": False,
            "expiration_value": "",
            "category": "politics",
            "risk_limit_cents": 100000,
            "rules_primary": "",
            "rules_secondary": "",
        }
        market_dao._db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )
        market_dao._db.collection.return_value.document.return_value.get.return_value.exists = (
            True
        )

        market = market_dao.get_market("TEST-2024")

        print(market)
        assert market is not None
        assert market.ticker == "TEST-2024"
        assert market.title == "Test Market"

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_get_market_not_found(self, mock_client, mock_init_app, market_dao):
        """Test market retrieval when market not found."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        market_dao._db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        market = market_dao.get_market("NONEXISTENT")

        assert market is None

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_update_market_success(
        self, mock_client, mock_init_app, market_dao, sample_market
    ):
        """Test successful market update."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        market_dao._db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )
        market_dao._db.collection.return_value.document.return_value.update.return_value = (
            None
        )

        result = market_dao.update_market(sample_market)

        assert result is True

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_update_market_not_found(
        self, mock_client, mock_init_app, market_dao, sample_market
    ):
        """Test market update when market not found."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        market_dao._db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = market_dao.update_market(sample_market)

        assert result is False

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_delete_market_success(self, mock_client, mock_init_app, market_dao):
        """Test successful market deletion."""
        market_dao._db.collection.return_value.document.return_value.delete.return_value = (
            None
        )

        result = market_dao.delete_market("TEST-2024")

        assert result is True

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_batch_create_markets_success(
        self, mock_client, mock_init_app, market_dao, sample_market
    ):
        """Test successful batch market creation."""
        markets = [sample_market]
        market_dao._db.bulk_writer.return_value.set.return_value = None

        result = market_dao.batch_create_markets(markets)

        assert result == 1

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_batch_create_markets_empty(self, mock_client, mock_init_app, market_dao):
        """Test batch create with empty list."""
        result = market_dao.batch_create_markets([])

        assert result == 0

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_batch_update_markets_success(
        self, mock_client, mock_init_app, market_dao, sample_market
    ):
        """Test successful batch market update."""
        markets = [sample_market]
        market_dao._db.bulk_writer.return_value.set.return_value = None

        result = market_dao.batch_update_markets(markets)

        assert result == 1

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.firestore.client")
    def test_get_markets_by_status(self, mock_client, mock_init_app, market_dao):
        """Test getting markets by status."""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "ticker": "TEST-2024",
            "event_ticker": "EVENT-2024",
            "market_type": "binary",
            "title": "Test Market",
            "subtitle": "Test Subtitle",
            "yes_sub_title": "Yes",
            "no_sub_title": "No",
            "status": "open",
            "open_time": datetime(2024, 1, 1),
            "close_time": datetime(2024, 12, 31),
            "expiration_time": datetime(2024, 12, 31),
            "latest_expiration_time": datetime(2024, 12, 31),
            "settlement_timer_seconds": 3600,
            "response_price_units": "cents",
            "notional_value": 10000,
            "notional_value_dollars": "100.00",
            "tick_size": 1,
            "yes_bid": 45,
            "yes_bid_dollars": "0.45",
            "yes_ask": 55,
            "yes_ask_dollars": "0.55",
            "no_bid": 45,
            "no_bid_dollars": "0.45",
            "no_ask": 55,
            "no_ask_dollars": "0.55",
            "last_price": 50,
            "last_price_dollars": "0.50",
            "previous_yes_bid": 45,
            "previous_yes_bid_dollars": "0.45",
            "previous_yes_ask": 55,
            "previous_yes_ask_dollars": "0.55",
            "previous_price": 50,
            "previous_price_dollars": "0.50",
            "volume": 1000,
            "volume_24h": 500,
            "liquidity": 5000,
            "liquidity_dollars": "50.00",
            "open_interest": 100,
            "result": "",
            "can_close_early": False,
            "expiration_value": "",
            "category": "politics",
            "risk_limit_cents": 100000,
            "rules_primary": "",
            "rules_secondary": "",
        }
        market_dao._db.collection.return_value.where.return_value.stream.return_value = [
            mock_doc
        ]

        markets = market_dao.get_markets_by_status("open")

        assert len(markets) == 1
        assert markets[0].status == "open"

    def test_close(self, market_dao):
        """Test closing Firebase connections."""
        with patch("firebase_admin.delete_app") as mock_delete_app:
            mock_app = MagicMock()
            market_dao._app = mock_app
            market_dao.close()

            mock_delete_app.assert_called_once_with(mock_app)
            assert market_dao._app is None
            assert market_dao._db is None

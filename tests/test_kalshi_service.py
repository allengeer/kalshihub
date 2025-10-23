"""Tests for the Kalshi API service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.kalshi.service import KalshiAPIService, Market, MarketsResponse


class TestKalshiAPIService:
    """Test cases for KalshiAPIService."""

    @pytest.fixture
    def service(self):
        """Create a KalshiAPIService instance for testing."""
        return KalshiAPIService()

    @pytest.fixture
    def sample_market_data(self):
        """Sample market data from API response."""
        return {
            "ticker": "TESTMARKET-2024",
            "event_ticker": "TESTEVENT-2024",
            "market_type": "binary",
            "title": "Test Market",
            "subtitle": "Test Subtitle",
            "yes_sub_title": "Yes",
            "no_sub_title": "No",
            "open_time": "2024-01-01T00:00:00Z",
            "close_time": "2024-12-31T23:59:59Z",
            "expiration_time": "2024-12-31T23:59:59Z",
            "latest_expiration_time": "2024-12-31T23:59:59Z",
            "settlement_timer_seconds": 3600,
            "status": "open",
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
            "previous_yes_bid": 44,
            "previous_yes_bid_dollars": "0.44",
            "previous_yes_ask": 56,
            "previous_yes_ask_dollars": "0.56",
            "previous_price": 49,
            "previous_price_dollars": "0.49",
            "volume": 1000,
            "volume_24h": 500,
            "liquidity": 2000,
            "liquidity_dollars": "20.00",
            "open_interest": 5000,
            "result": "unknown",
            "can_close_early": False,
            "expiration_value": "unknown",
            "category": "politics",
            "risk_limit_cents": 100000,
            "rules_primary": "Primary rules",
            "rules_secondary": "Secondary rules",
            "settlement_value": 0,
            "settlement_value_dollars": "0.00",
            "price_level_structure": "linear_cent",
            "price_ranges": [{"start": "0.00", "end": "1.00", "step": "0.01"}],
        }

    @pytest.fixture
    def sample_api_response(self, sample_market_data):
        """Sample API response data."""
        return {"cursor": "next_page_cursor", "markets": [sample_market_data]}

    def test_service_initialization(self):
        """Test KalshiAPIService initialization."""
        service = KalshiAPIService()
        assert service.base_url == "https://api.elections.kalshi.com/trade-api/v2"
        assert service._client is None

        # Test custom base URL
        custom_service = KalshiAPIService("https://custom.api.com")
        assert custom_service.base_url == "https://custom.api.com"

    def test_service_initialization_with_trailing_slash(self):
        """Test that trailing slashes are removed from base URL."""
        service = KalshiAPIService("https://api.example.com/")
        assert service.base_url == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with KalshiAPIService() as service:
            assert service._client is not None
            assert isinstance(service._client, httpx.AsyncClient)

        # Client should be closed after context exit
        assert service._client is None

    def test_parse_market(self, service, sample_market_data):
        """Test market data parsing."""
        market = service._parse_market(sample_market_data)

        assert isinstance(market, Market)
        assert market.ticker == "TESTMARKET-2024"
        assert market.event_ticker == "TESTEVENT-2024"
        assert market.title == "Test Market"
        assert market.status == "open"
        assert market.yes_bid == 45
        assert market.yes_ask == 55
        assert market.no_bid == 45
        assert market.no_ask == 55
        assert market.last_price == 50
        assert market.volume == 1000
        assert market.volume_24h == 500
        assert market.liquidity == 2000
        assert market.open_interest == 5000
        assert market.can_close_early is False
        assert market.category == "politics"
        assert market.risk_limit_cents == 100000
        assert len(market.price_ranges) == 1
        assert market.price_ranges[0]["start"] == "0.00"
        assert market.price_ranges[0]["end"] == "1.00"
        assert market.price_ranges[0]["step"] == "0.01"

        # Test datetime parsing
        assert isinstance(market.open_time, datetime)
        assert isinstance(market.close_time, datetime)
        assert isinstance(market.expiration_time, datetime)
        assert isinstance(market.latest_expiration_time, datetime)

    @pytest.mark.asyncio
    async def test_get_markets_success(self, service, sample_api_response):
        """Test successful get_markets call."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            service._client = mock_client

            response = await service.get_markets()

            assert isinstance(response, MarketsResponse)
            assert response.cursor == "next_page_cursor"
            assert len(response.markets) == 1

            market = response.markets[0]
            assert isinstance(market, Market)
            assert market.ticker == "TESTMARKET-2024"
            assert market.title == "Test Market"

            # Verify API call was made correctly
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert (
                call_args[0][0]
                == "https://api.elections.kalshi.com/trade-api/v2/markets"
            )
            assert call_args[1]["params"] == {}

    @pytest.mark.asyncio
    async def test_get_markets_with_parameters(self, service, sample_api_response):
        """Test get_markets with various parameters."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            service._client = mock_client

            response = await service.get_markets(
                limit=50,
                cursor="test_cursor",
                event_ticker="TESTEVENT",
                series_ticker="TESTSERIES",
                max_close_ts=1640995200,
                min_close_ts=1640995100,
                status="open,closed",
                tickers="MARKET1,MARKET2",
            )

            assert isinstance(response, MarketsResponse)

            # Verify API call was made with correct parameters
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            expected_params = {
                "limit": 50,
                "cursor": "test_cursor",
                "event_ticker": "TESTEVENT",
                "series_ticker": "TESTSERIES",
                "max_close_ts": 1640995200,
                "min_close_ts": 1640995100,
                "status": "open,closed",
                "tickers": "MARKET1,MARKET2",
            }
            assert call_args[1]["params"] == expected_params

    @pytest.mark.asyncio
    async def test_get_markets_invalid_limit(self, service):
        """Test get_markets with invalid limit parameter."""
        with pytest.raises(ValueError, match="limit must be between 1 and 1000"):
            await service.get_markets(limit=0)

        with pytest.raises(ValueError, match="limit must be between 1 and 1000"):
            await service.get_markets(limit=1001)

    @pytest.mark.asyncio
    async def test_get_markets_http_error(self, service):
        """Test get_markets with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Network error")
            mock_client_class.return_value = mock_client

            service._client = mock_client

            with pytest.raises(httpx.HTTPError, match="Failed to fetch markets"):
                await service.get_markets()

    @pytest.mark.asyncio
    async def test_get_markets_invalid_response_format(self, service):
        """Test get_markets with invalid response format."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"invalid": "response"}
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            service._client = mock_client

            with pytest.raises(ValueError, match="Invalid response format"):
                await service.get_markets()

    @pytest.mark.asyncio
    async def test_get_markets_empty_markets(self, service):
        """Test get_markets with empty markets list."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"cursor": "", "markets": []}
            mock_response.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            service._client = mock_client

            response = await service.get_markets()

            assert isinstance(response, MarketsResponse)
            assert response.cursor == ""
            assert len(response.markets) == 0

    @pytest.mark.asyncio
    async def test_close_client(self, service):
        """Test closing the HTTP client."""
        mock_client = AsyncMock()
        service._client = mock_client

        await service.close()

        mock_client.aclose.assert_called_once()
        assert service._client is None

    @pytest.mark.asyncio
    async def test_close_client_when_none(self, service):
        """Test closing client when it's already None."""
        service._client = None

        # Should not raise an exception
        await service.close()

        assert service._client is None

    def test_get_client_creates_new_client(self, service):
        """Test that _get_client creates a new client when none exists."""
        assert service._client is None

        client = service._get_client()

        assert service._client is not None
        assert client is service._client

    def test_get_client_returns_existing_client(self, service):
        """Test that _get_client returns existing client."""
        mock_client = AsyncMock()
        service._client = mock_client

        client = service._get_client()

        assert client is mock_client


class TestMarket:
    """Test cases for Market dataclass."""

    def test_market_creation(self):
        """Test Market dataclass creation."""
        market = Market(
            ticker="TEST-2024",
            event_ticker="EVENT-2024",
            market_type="binary",
            title="Test Market",
            subtitle="Test Subtitle",
            yes_sub_title="Yes",
            no_sub_title="No",
            open_time=datetime.now(),
            close_time=datetime.now(),
            expiration_time=datetime.now(),
            latest_expiration_time=datetime.now(),
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
            previous_yes_bid=44,
            previous_yes_bid_dollars="0.44",
            previous_yes_ask=56,
            previous_yes_ask_dollars="0.56",
            previous_price=49,
            previous_price_dollars="0.49",
            volume=1000,
            volume_24h=500,
            liquidity=2000,
            liquidity_dollars="20.00",
            open_interest=5000,
            result="unknown",
            can_close_early=False,
            expiration_value="unknown",
            category="politics",
            risk_limit_cents=100000,
            rules_primary="Primary rules",
            rules_secondary="Secondary rules",
            settlement_value=0,
            settlement_value_dollars="0.00",
            price_level_structure="linear_cent",
            price_ranges=[{"start": "0.00", "end": "1.00", "step": "0.01"}],
        )

        assert market.ticker == "TEST-2024"
        assert market.title == "Test Market"
        assert market.status == "open"
        assert market.yes_bid == 45
        assert market.volume == 1000
        assert market.can_close_early is False
        assert len(market.price_ranges) == 1


class TestMarketsResponse:
    """Test cases for MarketsResponse dataclass."""

    def test_markets_response_creation(self):
        """Test MarketsResponse dataclass creation."""
        market = Market(
            ticker="TEST-2024",
            event_ticker="EVENT-2024",
            market_type="binary",
            title="Test Market",
            subtitle="Test Subtitle",
            yes_sub_title="Yes",
            no_sub_title="No",
            open_time=datetime.now(),
            close_time=datetime.now(),
            expiration_time=datetime.now(),
            latest_expiration_time=datetime.now(),
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
            previous_yes_bid=44,
            previous_yes_bid_dollars="0.44",
            previous_yes_ask=56,
            previous_yes_ask_dollars="0.56",
            previous_price=49,
            previous_price_dollars="0.49",
            volume=1000,
            volume_24h=500,
            liquidity=2000,
            liquidity_dollars="20.00",
            open_interest=5000,
            result="unknown",
            can_close_early=False,
            expiration_value="unknown",
            category="politics",
            risk_limit_cents=100000,
            rules_primary="Primary rules",
            rules_secondary="Secondary rules",
            settlement_value=0,
            settlement_value_dollars="0.00",
            price_level_structure="linear_cent",
            price_ranges=[{"start": "0.00", "end": "1.00", "step": "0.01"}],
        )

        response = MarketsResponse(cursor="test_cursor", markets=[market])

        assert response.cursor == "test_cursor"
        assert len(response.markets) == 1
        assert response.markets[0].ticker == "TEST-2024"
        assert response.markets[0].ticker == "TEST-2024"
        assert response.markets[0].ticker == "TEST-2024"

"""Tests for Market Crawler."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.job import MarketCrawler
from src.kalshi.service import Market


class TestMarketCrawler:
    """Test cases for MarketCrawler."""

    @pytest.fixture
    def crawler(self):
        """Create a MarketCrawler instance for testing."""
        return MarketCrawler(
            firebase_project_id="test-project",
            firebase_credentials_path="test-credentials.json",
            max_retries=3,
            retry_delay_seconds=1,
        )

    @pytest.fixture
    def sample_markets(self):
        """Create sample markets for testing."""
        return [
            Market(
                ticker=f"TEST-{i}",
                event_ticker="EVENT-2024",
                market_type="binary",
                title=f"Test Market {i}",
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
            for i in range(5)
        ]

    def test_initialization(self, crawler):
        """Test crawler initialization."""
        assert crawler.firebase_project_id == "test-project"
        assert crawler.firebase_credentials_path == "test-credentials.json"
        # interval scheduling removed in single-run mode
        assert crawler.max_retries == 3
        assert crawler.retry_delay_seconds == 1
        # runner state removed in single-run mode

    @pytest.mark.asyncio
    async def test_initialize_services(self, crawler):
        """Test service initialization."""
        await crawler._initialize_services()

        assert crawler.kalshi_service is not None
        assert crawler.market_dao is not None

    @pytest.mark.asyncio
    async def test_crawl_markets_success(self, crawler, sample_markets):
        """Test successful market crawling."""
        # Initialize market_dao and kalshi_service
        crawler.market_dao = MagicMock()
        crawler.kalshi_service = AsyncMock()
        crawler.kalshi_service.__aenter__.return_value = crawler.kalshi_service
        crawler.kalshi_service.__aexit__.return_value = AsyncMock(return_value=None)
        crawler.kalshi_service.getAllOpenMarkets = AsyncMock(
            return_value=sample_markets
        )

        with patch.object(crawler, "_upsert_markets", return_value=5) as mock_upsert:
            result = await crawler._crawl_markets()

            assert result is True
            mock_upsert.assert_called_once_with(sample_markets)

    @pytest.mark.asyncio
    async def test_crawl_markets_no_markets(self, crawler):
        """Test crawling when no markets are available."""
        # Initialize kalshi_service
        crawler.kalshi_service = AsyncMock()
        crawler.kalshi_service.__aenter__.return_value = crawler.kalshi_service
        crawler.kalshi_service.__aexit__.return_value = AsyncMock(return_value=None)
        crawler.kalshi_service.getAllOpenMarkets = AsyncMock(return_value=[])

        result = await crawler._crawl_markets()

        assert result is True

    @pytest.mark.asyncio
    async def test_crawl_markets_api_failure(self, crawler):
        """Test crawling when API fails."""
        # Initialize kalshi_service
        crawler.kalshi_service = AsyncMock()
        crawler.kalshi_service.__aenter__.return_value = crawler.kalshi_service
        crawler.kalshi_service.__aexit__.return_value = AsyncMock(return_value=None)
        crawler.kalshi_service.getAllOpenMarkets = AsyncMock(
            side_effect=Exception("API Error")
        )

        result = await crawler._crawl_markets()

        assert result is False

    @pytest.mark.asyncio
    async def test_upsert_markets_success(self, crawler, sample_markets):
        """Test successful market upsert."""
        # Initialize market_dao
        crawler.market_dao = MagicMock()
        crawler.market_dao.batch_create_markets = MagicMock(return_value=3)

        result = await crawler._upsert_markets(sample_markets)

        assert result == 3
        crawler.market_dao.batch_create_markets.assert_called_once_with(sample_markets)

    @pytest.mark.asyncio
    async def test_upsert_markets_retry(self, crawler, sample_markets):
        """Test market upsert with retry logic."""
        # Initialize market_dao
        crawler.market_dao = MagicMock()
        crawler.market_dao.batch_create_markets = MagicMock(
            side_effect=[
                Exception("Error 1"),
                Exception("Error 2"),
                3,
            ]
        )

        result = await crawler._upsert_markets(sample_markets)

        assert result == 3
        assert crawler.market_dao.batch_create_markets.call_count == 3

    @pytest.mark.asyncio
    async def test_upsert_markets_max_retries(self, crawler, sample_markets):
        """Test market upsert when max retries exceeded."""
        # Initialize market_dao
        crawler.market_dao = MagicMock()
        crawler.market_dao.batch_create_markets = MagicMock(
            side_effect=Exception("Persistent Error")
        )

        result = await crawler._upsert_markets(sample_markets)

        assert result == 0
        assert crawler.market_dao.batch_create_markets.call_count == 3  # max_retries

    @pytest.mark.asyncio
    async def test_run_once_success(self, crawler, sample_markets):
        """Test running a single crawl cycle."""
        with patch.object(crawler, "_crawl_markets", return_value=True) as mock_crawl:
            result = await crawler.run_once()

            assert result is True
            mock_crawl.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_once_failure(self, crawler):
        """Test running a single crawl cycle that fails."""
        with patch.object(crawler, "_crawl_markets", return_value=False) as mock_crawl:
            result = await crawler.run_once()

            assert result is False
            mock_crawl.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, crawler):
        """Test closing the crawler."""
        # Set up mock services
        mock_kalshi = MagicMock()
        mock_kalshi.__aexit__ = AsyncMock()
        mock_dao = MagicMock()
        mock_dao.close = MagicMock()
        mock_event_dao = MagicMock()
        mock_event_dao.close = MagicMock()

        crawler.kalshi_service = mock_kalshi
        crawler.market_dao = mock_dao
        crawler.engine_event_dao = mock_event_dao

        await crawler.close()

        mock_kalshi.__aexit__.assert_called_once_with(None, None, None)
        mock_dao.close.assert_called_once()
        mock_event_dao.close.assert_called_once()

    # Single-run design has no module-level main entrypoint; those tests removed

"""Tests for Market Crawler."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.firebase import MarketCrawler
from src.kalshi.service import Market


@pytest.mark.skip(
    reason="TODO: Fix mocking issues with AsyncIOScheduler and async context managers"
)
class TestMarketCrawler:
    """Test cases for MarketCrawler."""

    @pytest.fixture
    def crawler(self):
        """Create a MarketCrawler instance for testing."""
        return MarketCrawler(
            firebase_project_id="test-project",
            firebase_credentials_path="test-credentials.json",
            interval_minutes=30,
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
        assert crawler.interval_minutes == 30
        assert crawler.max_retries == 3
        assert crawler.retry_delay_seconds == 1
        assert crawler.is_running is False

    @pytest.mark.asyncio
    async def test_initialize_services(self, crawler):
        """Test service initialization."""
        await crawler._initialize_services()

        assert crawler.kalshi_service is not None
        assert crawler.market_dao is not None

    @pytest.mark.asyncio
    async def test_crawl_markets_success(self, crawler, sample_markets):
        """Test successful market crawling."""
        with patch.object(crawler, "_initialize_services") as mock_init, patch(
            "src.kalshi.service.KalshiAPIService"
        ) as mock_kalshi_class:

            mock_kalshi = AsyncMock()
            mock_kalshi.__aenter__.return_value = mock_kalshi
            mock_kalshi.__aexit__.return_value = None
            mock_kalshi.getAllOpenMarkets.return_value = sample_markets
            mock_kalshi_class.return_value = mock_kalshi

            with patch.object(
                crawler, "_upsert_markets", return_value=5
            ) as mock_upsert:

                result = await crawler._crawl_markets()

                assert result is True
                mock_init.assert_called_once()
                mock_upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_markets_no_markets(self, crawler):
        """Test crawling when no markets are available."""
        with patch.object(crawler, "_initialize_services") as mock_init, patch(
            "src.kalshi.service.KalshiAPIService"
        ) as mock_kalshi_class:

            mock_kalshi = AsyncMock()
            mock_kalshi.__aenter__.return_value = mock_kalshi
            mock_kalshi.__aexit__.return_value = None
            mock_kalshi.getAllOpenMarkets.return_value = []
            mock_kalshi_class.return_value = mock_kalshi

            result = await crawler._crawl_markets()

            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_markets_api_failure(self, crawler):
        """Test crawling when API fails."""
        with patch.object(crawler, "_initialize_services") as mock_init, patch(
            "src.kalshi.service.KalshiAPIService"
        ) as mock_kalshi_class:

            mock_kalshi = AsyncMock()
            mock_kalshi.__aenter__.return_value = mock_kalshi
            mock_kalshi.__aexit__.return_value = None
            mock_kalshi.getAllOpenMarkets.side_effect = Exception("API Error")
            mock_kalshi_class.return_value = mock_kalshi

            result = await crawler._crawl_markets()

            assert result is False
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_markets_success(self, crawler, sample_markets):
        """Test successful market upsert."""
        with patch.object(
            crawler.market_dao, "batch_create_markets", return_value=3
        ) as mock_upsert:
            result = await crawler._upsert_markets(sample_markets)

            assert result == 3
            mock_upsert.assert_called_once_with(sample_markets)

    @pytest.mark.asyncio
    async def test_upsert_markets_retry(self, crawler, sample_markets):
        """Test market upsert with retry logic."""
        with patch.object(crawler.market_dao, "batch_create_markets") as mock_upsert:
            mock_upsert.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                3,
            ]

            result = await crawler._upsert_markets(sample_markets)

            assert result == 3
            assert mock_upsert.call_count == 3

    @pytest.mark.asyncio
    async def test_upsert_markets_max_retries(self, crawler, sample_markets):
        """Test market upsert when max retries exceeded."""
        with patch.object(crawler.market_dao, "batch_create_markets") as mock_upsert:
            mock_upsert.side_effect = Exception("Persistent Error")

            result = await crawler._upsert_markets(sample_markets)

            assert result == 0
            assert mock_upsert.call_count == 3  # max_retries

    def test_start_crawler(self, crawler):
        """Test starting the crawler."""
        with patch.object(crawler.scheduler, "running", False):
            crawler.start()

            assert crawler.scheduler.running is True

    def test_start_crawler_already_running(self, crawler):
        """Test starting crawler when already running."""
        with patch.object(crawler.scheduler, "running", True):
            crawler.start()

            # Should not raise an error or change state

    def test_stop_crawler(self, crawler):
        """Test stopping the crawler."""
        with patch.object(crawler.scheduler, "running", True):
            crawler.stop()

            assert crawler.scheduler.running is False

    def test_stop_crawler_not_running(self, crawler):
        """Test stopping crawler when not running."""
        with patch.object(crawler.scheduler, "running", False):
            crawler.stop()

            # Should not raise an error

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
        with patch.object(crawler, "stop") as mock_stop, patch.object(
            crawler.kalshi_service, "close"
        ) as mock_kalshi_close, patch.object(
            crawler.market_dao, "close"
        ) as mock_dao_close:

            crawler.kalshi_service = MagicMock()
            crawler.market_dao = MagicMock()

            await crawler.close()

            mock_stop.assert_called_once()
            mock_kalshi_close.assert_called_once()
            mock_dao_close.assert_called_once()

    def test_get_status(self, crawler):
        """Test getting crawler status."""
        with patch.object(crawler.scheduler, "running", True), patch.object(
            crawler.scheduler, "get_job"
        ) as mock_get_job:

            mock_job = MagicMock()
            mock_job.next_run_time = datetime(2024, 1, 1, 12, 0, 0)
            mock_get_job.return_value = mock_job

            status = crawler.get_status()

            assert status["is_running"] is True
            assert status["is_crawling"] is False
            assert status["interval_minutes"] == 30
            assert status["max_retries"] == 3
            assert status["retry_delay_seconds"] == 1
            assert status["next_run_time"] == datetime(2024, 1, 1, 12, 0, 0)

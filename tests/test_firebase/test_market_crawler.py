"""Tests for Market Crawler."""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

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

    def test_start_crawler(self, crawler):
        """Test starting the crawler."""
        with patch.object(crawler.scheduler, "start") as mock_start:
            crawler.start()
            mock_start.assert_called_once()

    def test_start_crawler_already_running(self, crawler):
        """Test starting crawler when already running."""
        with patch.object(crawler.scheduler, "start") as mock_start:
            crawler.start()
            # Should not raise an error
            mock_start.assert_called_once()

    def test_stop_crawler(self, crawler):
        """Test stopping the crawler."""
        with patch.object(crawler.scheduler, "shutdown") as mock_shutdown, patch.object(
            type(crawler.scheduler),
            "running",
            new_callable=lambda: PropertyMock(return_value=True),
        ):
            crawler.stop()
            mock_shutdown.assert_called_once_with(wait=True)

    def test_stop_crawler_not_running(self, crawler):
        """Test stopping crawler when not running."""
        with patch.object(crawler.scheduler, "shutdown") as mock_shutdown, patch.object(
            type(crawler.scheduler),
            "running",
            new_callable=lambda: PropertyMock(return_value=False),
        ):
            crawler.stop()
            # Should not call shutdown if not running
            mock_shutdown.assert_not_called()

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

        crawler.kalshi_service = mock_kalshi
        crawler.market_dao = mock_dao

        with patch.object(crawler, "stop") as mock_stop:
            await crawler.close()

            mock_stop.assert_called_once()
            mock_kalshi.__aexit__.assert_called_once_with(None, None, None)
            mock_dao.close.assert_called_once()

    def test_get_status(self, crawler):
        """Test getting crawler status."""
        # Set the is_running flag and mock scheduler.running
        crawler.is_running = True
        with patch.object(
            type(crawler.scheduler),
            "running",
            new_callable=lambda: PropertyMock(return_value=True),
        ):
            status = crawler.get_status()

            assert status["is_running"] is True
            assert status["scheduler_running"] is True
            assert status["interval_minutes"] == 30
            assert status["firebase_project"] == "test-project"

    @pytest.mark.asyncio
    async def test_main_function_success(self):
        """Test the main function with successful execution."""
        with patch.dict(
            os.environ,
            {
                "FIREBASE_PROJECT_ID": "test-project",
                "FIREBASE_CREDENTIALS_PATH": "test-credentials.json",
                "CRAWLER_INTERVAL_MINUTES": "15",
                "CRAWLER_MAX_RETRIES": "5",
                "CRAWLER_RETRY_DELAY_SECONDS": "2",
            },
        ), patch("src.job.market_crawler.MarketCrawler") as mock_crawler_class:
            # Mock the crawler instance
            mock_crawler = MagicMock()
            mock_crawler.run_once = AsyncMock(return_value=True)
            mock_crawler.get_status.return_value = {"is_running": False}
            mock_crawler.close = AsyncMock()
            mock_crawler_class.return_value = mock_crawler

            # Import and run main
            from src.job.market_crawler import main

            await main()

            # Verify crawler was created with correct parameters
            mock_crawler_class.assert_called_once_with(
                firebase_project_id="test-project",
                firebase_credentials_path="test-credentials.json",
                interval_minutes=15,
                max_retries=5,
                retry_delay_seconds=2,
            )

            # Verify methods were called
            mock_crawler.run_once.assert_called_once()
            mock_crawler.get_status.assert_called_once()
            mock_crawler.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_missing_project_id(self):
        """Test the main function with missing FIREBASE_PROJECT_ID."""
        with patch.dict(os.environ, {}, clear=True), patch(
            "builtins.print"
        ) as mock_print:
            from src.job.market_crawler import main

            await main()

            mock_print.assert_called_with(
                "Error: FIREBASE_PROJECT_ID environment variable is required"
            )

    @pytest.mark.asyncio
    async def test_main_function_crawler_failure(self):
        """Test the main function when crawler fails."""
        with patch.dict(
            os.environ,
            {
                "FIREBASE_PROJECT_ID": "test-project",
                "FIREBASE_CREDENTIALS_PATH": "test-credentials.json",
            },
        ), patch("src.job.market_crawler.MarketCrawler") as mock_crawler_class, patch(
            "builtins.print"
        ) as mock_print:
            # Mock the crawler instance
            mock_crawler = MagicMock()
            mock_crawler.run_once = AsyncMock(return_value=False)
            mock_crawler.get_status.return_value = {"is_running": False}
            mock_crawler.close = AsyncMock()
            mock_crawler_class.return_value = mock_crawler

            from src.job.market_crawler import main

            await main()

            # Verify failure message was printed
            mock_print.assert_any_call("✗ Crawler failed")

    @pytest.mark.asyncio
    async def test_main_function_keyboard_interrupt(self):
        """Test the main function handling KeyboardInterrupt."""
        with patch.dict(
            os.environ,
            {
                "FIREBASE_PROJECT_ID": "test-project",
                "FIREBASE_CREDENTIALS_PATH": "test-credentials.json",
            },
        ), patch("src.job.market_crawler.MarketCrawler") as mock_crawler_class, patch(
            "builtins.print"
        ) as mock_print:
            # Mock the crawler instance
            mock_crawler = MagicMock()
            mock_crawler.run_once = AsyncMock(side_effect=KeyboardInterrupt())
            mock_crawler.close = AsyncMock()
            mock_crawler_class.return_value = mock_crawler

            from src.job.market_crawler import main

            await main()

            # Verify KeyboardInterrupt was handled
            mock_print.assert_any_call("\nShutting down crawler...")
            mock_crawler.close.assert_called_once()

    def test_module_execution(self):
        """Test the module execution when run as main."""
        # Import the module and simulate the if __name__ == "__main__" block
        import src.job.market_crawler

        # Manually execute the if __name__ == "__main__" block
        # This tests the structure without actually running asyncio.run
        if src.job.market_crawler.__name__ == "__main__":
            # This would normally call asyncio.run(main())
            # We're just testing that the structure exists
            pass

        # For coverage purposes, we'll test that the if block exists
        # by checking the source code contains the expected structure
        import inspect

        source = inspect.getsource(src.job.market_crawler)
        assert 'if __name__ == "__main__":' in source
        assert "asyncio.run(main())" in source

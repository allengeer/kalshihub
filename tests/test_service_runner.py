"""Tests for Kalshihub Service Runner."""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.service_runner import KalshihubServiceRunner


class TestKalshihubServiceRunner:
    """Test cases for KalshihubServiceRunner."""

    @pytest.fixture
    def service_runner(self):
        """Create a KalshihubServiceRunner instance for testing."""
        return KalshihubServiceRunner(
            firebase_project_id="test-project",
            firebase_credentials_path="test-credentials.json",
            crawler_interval_minutes=5,
            market_close_window_hours=24,
        )

    def test_initialization(self, service_runner):
        """Test service runner initialization."""
        assert service_runner.firebase_project_id == "test-project"
        assert service_runner.firebase_credentials_path == "test-credentials.json"
        assert service_runner.crawler_interval_minutes == 5
        assert service_runner.market_close_window_hours == 24
        assert service_runner.is_running is False
        assert service_runner.market_crawler is None

    @pytest.mark.asyncio
    async def test_initialize_services(self, service_runner):
        """Test service initialization."""
        with patch("src.service_runner.MarketCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            await service_runner._initialize_services()

            assert service_runner.market_crawler is not None
            mock_crawler_class.assert_called_once_with(
                firebase_project_id="test-project",
                firebase_credentials_path="test-credentials.json",
                kalshi_base_url="https://api.elections.kalshi.com/trade-api/v2",
                kalshi_rate_limit=20.0,
                interval_minutes=5,
                max_retries=3,
                retry_delay_seconds=1,
            )

    @pytest.mark.asyncio
    async def test_get_market_close_timestamp(self, service_runner):
        """Test market close timestamp calculation."""
        # Mock datetime.now() to return a fixed time
        with patch("src.service_runner.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.fromtimestamp = datetime.fromtimestamp

            timestamp = await service_runner._get_market_close_timestamp()

            # Should be 24 hours from the mocked time
            expected_time = datetime(2024, 1, 2, 12, 0, 0)
            assert timestamp == int(expected_time.timestamp())

    @pytest.mark.asyncio
    async def test_run_market_crawler_with_filtering_success(self, service_runner):
        """Test running market crawler with filtering successfully."""
        # Mock the market crawler
        mock_crawler = MagicMock()
        mock_crawler._crawl_markets_with_filtering = AsyncMock(return_value=True)
        service_runner.market_crawler = mock_crawler

        # Mock the timestamp calculation
        with patch.object(
            service_runner, "_get_market_close_timestamp"
        ) as mock_timestamp:
            mock_timestamp.return_value = 1704110400  # Fixed timestamp

            await service_runner._run_market_crawler_with_filtering()

            mock_timestamp.assert_called_once()
            mock_crawler._crawl_markets_with_filtering.assert_called_once_with(
                1704110400
            )

    @pytest.mark.asyncio
    async def test_run_market_crawler_with_filtering_no_crawler(self, service_runner):
        """Test running market crawler when crawler is not initialized."""
        # Don't set market_crawler
        service_runner.market_crawler = None

        # Should not raise an exception
        await service_runner._run_market_crawler_with_filtering()

    @pytest.mark.asyncio
    async def test_run_market_crawler_with_filtering_error(self, service_runner):
        """Test running market crawler with filtering when an error occurs."""
        # Mock the market crawler to raise an exception
        mock_crawler = MagicMock()
        mock_crawler._crawl_markets_with_filtering = AsyncMock(
            side_effect=Exception("Test error")
        )
        service_runner.market_crawler = mock_crawler

        # Mock the timestamp calculation
        with patch.object(
            service_runner, "_get_market_close_timestamp"
        ) as mock_timestamp:
            mock_timestamp.return_value = 1704110400

            # Should not raise an exception
            await service_runner._run_market_crawler_with_filtering()

    @pytest.mark.asyncio
    async def test_start_success(self, service_runner):
        """Test successful service startup."""
        with patch.object(
            service_runner, "_setup_signal_handlers"
        ) as mock_setup, patch.object(
            service_runner, "_initialize_services"
        ) as mock_init, patch.object(
            service_runner, "shutdown_event"
        ) as mock_shutdown:
            # Mock the market crawler
            mock_crawler = MagicMock()
            mock_crawler.start = AsyncMock()
            service_runner.market_crawler = mock_crawler

            # Mock the shutdown event to complete immediately
            mock_shutdown.wait = AsyncMock()

            await service_runner.start()

            mock_setup.assert_called_once()
            mock_init.assert_called_once()
            mock_crawler.start.assert_called_once()
            assert service_runner.is_running is True

    @pytest.mark.asyncio
    async def test_start_with_error(self, service_runner):
        """Test service startup with error."""
        with patch.object(
            service_runner, "_initialize_services"
        ) as mock_init, patch.object(service_runner, "shutdown") as mock_shutdown:
            mock_init.side_effect = Exception("Initialization error")

            await service_runner.start()

            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_success(self, service_runner):
        """Test successful service shutdown."""
        service_runner.is_running = True
        mock_crawler = MagicMock()
        mock_crawler.close = AsyncMock()
        service_runner.market_crawler = mock_crawler

        await service_runner.shutdown()

        mock_crawler.close.assert_called_once()
        assert service_runner.is_running is False

    @pytest.mark.asyncio
    async def test_shutdown_when_not_running(self, service_runner):
        """Test shutdown when service is not running."""
        service_runner.is_running = False

        # Should not raise an exception
        await service_runner.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_with_error(self, service_runner):
        """Test shutdown with error."""
        service_runner.is_running = True
        mock_crawler = MagicMock()
        mock_crawler.close = AsyncMock(side_effect=Exception("Close error"))
        service_runner.market_crawler = mock_crawler

        # Should not raise an exception
        await service_runner.shutdown()

    def test_get_status(self, service_runner):
        """Test getting service status."""
        service_runner.is_running = True
        mock_crawler = MagicMock()
        mock_crawler.get_status.return_value = {"is_running": True}
        service_runner.market_crawler = mock_crawler

        status = service_runner.get_status()

        assert status["is_running"] is True
        assert status["firebase_project"] == "test-project"
        assert status["crawler_interval_minutes"] == 5
        assert status["market_close_window_hours"] == 24
        assert "services" in status
        assert "market_crawler" in status["services"]

    def test_get_status_no_crawler(self, service_runner):
        """Test getting status when crawler is not initialized."""
        service_runner.is_running = True
        service_runner.market_crawler = None

        status = service_runner.get_status()

        assert status["is_running"] is True
        assert "services" in status
        assert status["services"] == {}

    @pytest.mark.asyncio
    async def test_main_function_success(self):
        """Test the main function with successful execution."""
        with patch.dict(
            os.environ,
            {
                "FIREBASE_PROJECT_ID": "test-project",
                "FIREBASE_CREDENTIALS_PATH": "test-credentials.json",
                "CRAWLER_INTERVAL_MINUTES": "10",
                "MARKET_CLOSE_WINDOW_HOURS": "48",
            },
        ), patch("src.service_runner.KalshihubServiceRunner") as mock_runner_class:
            # Mock the service runner instance
            mock_runner = MagicMock()
            mock_runner.start = AsyncMock()
            mock_runner.shutdown = AsyncMock()
            mock_runner_class.return_value = mock_runner

            from src.service_runner import main

            await main()

            # Verify service runner was created with correct parameters
            mock_runner_class.assert_called_once_with(
                firebase_project_id="test-project",
                firebase_credentials_path="test-credentials.json",
                kalshi_base_url="https://api.elections.kalshi.com/trade-api/v2",
                kalshi_rate_limit=20.0,
                crawler_interval_minutes=10,
                market_close_window_hours=48,
                max_retries=3,
                retry_delay_seconds=1,
            )

            # Verify methods were called
            mock_runner.start.assert_called_once()
            mock_runner.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_missing_project_id(self):
        """Test the main function with missing FIREBASE_PROJECT_ID."""
        with patch.dict(os.environ, {}, clear=True), patch(
            "builtins.print"
        ) as mock_print:
            from src.service_runner import main

            await main()

            mock_print.assert_called_with(
                "Error: FIREBASE_PROJECT_ID environment variable is required"
            )

    @pytest.mark.asyncio
    async def test_main_function_keyboard_interrupt(self):
        """Test the main function handling KeyboardInterrupt."""
        with patch.dict(
            os.environ,
            {
                "FIREBASE_PROJECT_ID": "test-project",
                "FIREBASE_CREDENTIALS_PATH": "test-credentials.json",
            },
        ), patch(
            "src.service_runner.KalshihubServiceRunner"
        ) as mock_runner_class, patch(
            "builtins.print"
        ) as mock_print:
            # Mock the service runner instance
            mock_runner = MagicMock()
            mock_runner.start = AsyncMock(side_effect=KeyboardInterrupt())
            mock_runner.shutdown = AsyncMock()
            mock_runner_class.return_value = mock_runner

            from src.service_runner import main

            await main()

            # Verify KeyboardInterrupt was handled
            mock_print.assert_any_call(
                "\nReceived keyboard interrupt, shutting down..."
            )
            mock_runner.shutdown.assert_called_once()

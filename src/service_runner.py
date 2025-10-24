"""Kalshihub Service Runner - Main entry point for the application."""

import asyncio
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.job import MarketCrawler


class KalshihubServiceRunner:
    """Main service runner that orchestrates all Kalshihub services."""

    def __init__(
        self,
        firebase_project_id: str,
        firebase_credentials_path: Optional[str] = None,
        kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2",
        kalshi_rate_limit: float = 20.0,
        crawler_interval_minutes: int = 5,
        market_close_window_hours: int = 24,
        max_retries: int = 3,
        retry_delay_seconds: int = 1,
    ):
        """Initialize the service runner.

        Args:
            firebase_project_id: Firebase project ID
            firebase_credentials_path: Path to Firebase service account credentials
            kalshi_base_url: Kalshi API base URL
            kalshi_rate_limit: Kalshi API rate limit (requests per second)
            crawler_interval_minutes: Market crawler interval in minutes
            market_close_window_hours: Hours ahead to crawl markets
                (e.g., 24 for next 24 hours)
            max_retries: Maximum number of retries for failed operations
            retry_delay_seconds: Initial delay between retries (exponential backoff)
        """
        self.firebase_project_id = firebase_project_id
        self.firebase_credentials_path = firebase_credentials_path
        self.kalshi_base_url = kalshi_base_url
        self.kalshi_rate_limit = kalshi_rate_limit
        self.crawler_interval_minutes = crawler_interval_minutes
        self.market_close_window_hours = market_close_window_hours
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        self.market_crawler: Optional[MarketCrawler] = None
        self.is_running = False
        self.shutdown_event = asyncio.Event()

    async def _initialize_services(self):
        """Initialize all services."""
        print(f"[{datetime.now()}] Initializing Kalshihub services...")
        sys.stdout.flush()

        # Initialize market crawler with close time filtering
        self.market_crawler = MarketCrawler(
            firebase_project_id=self.firebase_project_id,
            firebase_credentials_path=self.firebase_credentials_path,
            kalshi_base_url=self.kalshi_base_url,
            kalshi_rate_limit=self.kalshi_rate_limit,
            interval_minutes=self.crawler_interval_minutes,
            max_retries=self.max_retries,
            retry_delay_seconds=self.retry_delay_seconds,
        )

        print(f"[{datetime.now()}] Services initialized successfully")
        sys.stdout.flush()

    async def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            print(
                f"\n[{datetime.now()}] Received signal {signum}, "
                "initiating graceful shutdown..."
            )
            sys.stdout.flush()
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _get_market_close_timestamp(self) -> int:
        """Get the Unix timestamp for the market close window.

        Returns:
            Unix timestamp for markets closing within the specified window
        """
        close_time = datetime.now() + timedelta(hours=self.market_close_window_hours)
        return int(close_time.timestamp())

    async def _run_market_crawler_with_filtering(self):
        """Run the market crawler with close time filtering."""
        if not self.market_crawler:
            print(f"[{datetime.now()}] Market crawler not initialized")
            sys.stdout.flush()
            return

        try:
            # Get the max close timestamp for filtering
            max_close_ts = await self._get_market_close_timestamp()

            print(
                f"[{datetime.now()}] Running market crawler for markets closing "
                f"within next {self.market_close_window_hours} hours "
                f"(before {datetime.fromtimestamp(max_close_ts)})"
            )
            sys.stdout.flush()

            # Run the crawler with filtering
            await self.market_crawler._crawl_markets_with_filtering(max_close_ts)

        except Exception as e:
            print(f"[{datetime.now()}] Market crawler error: {e}")
            sys.stdout.flush()

    async def start(self):
        """Start all services."""
        try:
            print(f"[{datetime.now()}] Starting Kalshihub Service Runner...")
            sys.stdout.flush()

            # Set up signal handlers
            await self._setup_signal_handlers()

            # Initialize services
            await self._initialize_services()

            # Start market crawler
            if self.market_crawler:
                await self.market_crawler.start()
                print(
                    f"[{datetime.now()}] Market crawler started with "
                    f"{self.crawler_interval_minutes}-minute interval"
                )
                sys.stdout.flush()

            self.is_running = True
            print(f"[{datetime.now()}] Kalshihub Service Runner started successfully")
            sys.stdout.flush()

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except Exception as e:
            print(f"[{datetime.now()}] Service runner error: {e}")
            sys.stdout.flush()
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown all services."""
        if not self.is_running:
            return

        print(f"[{datetime.now()}] Shutting down Kalshihub Service Runner...")
        sys.stdout.flush()

        try:
            # Stop market crawler
            if self.market_crawler:
                await self.market_crawler.close()
                print(f"[{datetime.now()}] Market crawler stopped")
                sys.stdout.flush()

            self.is_running = False
            self.shutdown_event.set()

            print(f"[{datetime.now()}] Kalshihub Service Runner shutdown complete")
            sys.stdout.flush()

        except Exception as e:
            print(f"[{datetime.now()}] Error during shutdown: {e}")
            sys.stdout.flush()

    def get_status(self) -> Dict:
        """Get the current status of all services.

        Returns:
            Dictionary containing status information
        """
        status = {
            "is_running": self.is_running,
            "firebase_project": self.firebase_project_id,
            "crawler_interval_minutes": self.crawler_interval_minutes,
            "market_close_window_hours": self.market_close_window_hours,
            "services": {},
        }

        if self.market_crawler:
            crawler_status = self.market_crawler.get_status()
            status["services"]["market_crawler"] = crawler_status  # type: ignore

        return status


async def main():
    """Main function for the service runner."""
    # Load configuration from environment variables
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    kalshi_base_url = os.getenv(
        "KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2"
    )
    kalshi_rate_limit = float(os.getenv("KALSHI_RATE_LIMIT", "20.0"))
    crawler_interval_minutes = int(os.getenv("CRAWLER_INTERVAL_MINUTES", "5"))
    market_close_window_hours = int(os.getenv("MARKET_CLOSE_WINDOW_HOURS", "24"))
    max_retries = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
    retry_delay_seconds = int(os.getenv("CRAWLER_RETRY_DELAY_SECONDS", "1"))

    if not firebase_project_id:
        print("Error: FIREBASE_PROJECT_ID environment variable is required")
        return

    # Create and start service runner
    service_runner = KalshihubServiceRunner(
        firebase_project_id=firebase_project_id,
        firebase_credentials_path=firebase_credentials_path,
        kalshi_base_url=kalshi_base_url,
        kalshi_rate_limit=kalshi_rate_limit,
        crawler_interval_minutes=crawler_interval_minutes,
        market_close_window_hours=market_close_window_hours,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
    )

    try:
        await service_runner.start()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    finally:
        await service_runner.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

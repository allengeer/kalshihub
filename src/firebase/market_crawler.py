"""Market Crawler service for automated market data refresh."""

import asyncio
import os
from datetime import datetime
from typing import List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.kalshi.service import KalshiAPIService, Market
from .market_dao import MarketDAO


class MarketCrawler:
    """Automated service to refresh market data at regular intervals."""

    def __init__(
        self,
        firebase_project_id: str,
        firebase_credentials_path: Optional[str] = None,
        kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2",
        kalshi_rate_limit: float = 20.0,
        interval_minutes: int = 30,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay_seconds: int = 1,
    ):
        """Initialize Market Crawler.

        Args:
            firebase_project_id: Firebase project ID
            firebase_credentials_path: Path to Firebase service account credentials
            kalshi_base_url: Kalshi API base URL
            kalshi_rate_limit: Kalshi API rate limit (requests per second)
            interval_minutes: Crawl interval in minutes
            batch_size: Batch size for database operations
            max_retries: Maximum number of retries for failed operations
            retry_delay_seconds: Initial delay between retries (exponential backoff)
        """
        self.firebase_project_id = firebase_project_id
        self.firebase_credentials_path = firebase_credentials_path
        self.kalshi_base_url = kalshi_base_url
        self.kalshi_rate_limit = kalshi_rate_limit
        self.interval_minutes = interval_minutes
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        self.scheduler = AsyncIOScheduler()
        self.kalshi_service: Optional[KalshiAPIService] = None
        self.market_dao: Optional[MarketDAO] = None
        self.is_running = False

    async def _initialize_services(self):
        """Initialize Kalshi API service and Market DAO."""
        if not self.kalshi_service:
            self.kalshi_service = KalshiAPIService(
                base_url=self.kalshi_base_url,
                rate_limit=self.kalshi_rate_limit,
            )

        if not self.market_dao:
            self.market_dao = MarketDAO(
                project_id=self.firebase_project_id,
                credentials_path=self.firebase_credentials_path,
            )

    async def _crawl_markets(self) -> bool:
        """Crawl and update market data.

        Returns:
            True if crawl was successful, False otherwise
        """
        try:
            await self._initialize_services()

            print(f"[{datetime.now()}] Starting market crawl...")

            # Get all open markets from Kalshi API
            async with self.kalshi_service as kalshi:
                markets = await kalshi.getAllOpenMarkets()

            print(f"[{datetime.now()}] Retrieved {len(markets)} open markets")

            if not markets:
                print(f"[{datetime.now()}] No markets to process")
                return True

            # Process markets in batches
            success_count = 0
            total_batches = (len(markets) + self.batch_size - 1) // self.batch_size

            for i in range(0, len(markets), self.batch_size):
                batch = markets[i : i + self.batch_size]
                batch_num = (i // self.batch_size) + 1

                print(
                    f"[{datetime.now()}] Processing batch {batch_num}/{total_batches} ({len(batch)} markets)"
                )

                # Try to update existing markets first, then create new ones
                updated_count = await self._update_existing_markets(batch)
                created_count = await self._create_new_markets(batch)

                batch_success = updated_count + created_count
                success_count += batch_success

                print(
                    f"[{datetime.now()}] Batch {batch_num} completed: {batch_success}/{len(batch)} markets processed"
                )

            print(
                f"[{datetime.now()}] Crawl completed: {success_count}/{len(markets)} markets processed successfully"
            )
            return success_count > 0

        except Exception as e:
            print(f"[{datetime.now()}] Crawl failed: {e}")
            return False

    async def _update_existing_markets(self, markets: List[Market]) -> int:
        """Update existing markets with exponential backoff retry.

        Args:
            markets: List of markets to update

        Returns:
            Number of successfully updated markets
        """
        if not self.market_dao:
            return 0

        for attempt in range(self.max_retries):
            try:
                return self.market_dao.batch_update_markets(markets)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_seconds * (2**attempt)
                    print(
                        f"[{datetime.now()}] Update attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    print(f"[{datetime.now()}] All update attempts failed: {e}")
                    return 0

        return 0

    async def _create_new_markets(self, markets: List[Market]) -> int:
        """Create new markets with exponential backoff retry.

        Args:
            markets: List of markets to create

        Returns:
            Number of successfully created markets
        """
        if not self.market_dao:
            return 0

        for attempt in range(self.max_retries):
            try:
                return self.market_dao.batch_create_markets(markets)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_seconds * (2**attempt)
                    print(
                        f"[{datetime.now()}] Create attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    print(f"[{datetime.now()}] All create attempts failed: {e}")
                    return 0

        return 0

    async def _crawl_job(self):
        """Scheduled job to crawl markets."""
        if self.is_running:
            print(
                f"[{datetime.now()}] Previous crawl still running, skipping this cycle"
            )
            return

        self.is_running = True
        try:
            await self._crawl_markets()
        finally:
            self.is_running = False

    def start(self):
        """Start the market crawler scheduler."""
        if self.scheduler.running:
            print("Crawler is already running")
            return

        # Schedule the crawl job
        self.scheduler.add_job(
            self._crawl_job,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="market_crawl",
            name="Market Data Crawl",
            replace_existing=True,
        )

        self.scheduler.start()
        print(
            f"[{datetime.now()}] Market crawler started - will run every {self.interval_minutes} minutes"
        )

    def stop(self):
        """Stop the market crawler scheduler."""
        if not self.scheduler.running:
            print("Crawler is not running")
            return

        self.scheduler.shutdown()
        print(f"[{datetime.now()}] Market crawler stopped")

    async def run_once(self) -> bool:
        """Run a single crawl cycle immediately.

        Returns:
            True if crawl was successful, False otherwise
        """
        return await self._crawl_markets()

    async def close(self):
        """Close all connections and cleanup resources."""
        self.stop()

        if self.kalshi_service:
            await self.kalshi_service.close()

        if self.market_dao:
            self.market_dao.close()

    def get_status(self) -> dict:
        """Get crawler status information.

        Returns:
            Dictionary with crawler status
        """
        return {
            "is_running": self.scheduler.running,
            "is_crawling": self.is_running,
            "interval_minutes": self.interval_minutes,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "next_run_time": (
                self.scheduler.get_job("market_crawl").next_run_time
                if self.scheduler.running
                else None
            ),
        }


async def main():
    """Main function for testing the crawler."""
    # Load configuration from environment variables
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    interval_minutes = int(os.getenv("CRAWLER_INTERVAL_MINUTES", "30"))
    batch_size = int(os.getenv("CRAWLER_BATCH_SIZE", "100"))
    max_retries = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
    retry_delay_seconds = int(os.getenv("CRAWLER_RETRY_DELAY_SECONDS", "1"))

    if not firebase_project_id:
        print("Error: FIREBASE_PROJECT_ID environment variable is required")
        return

    # Create and start crawler
    crawler = MarketCrawler(
        firebase_project_id=firebase_project_id,
        firebase_credentials_path=firebase_credentials_path,
        interval_minutes=interval_minutes,
        batch_size=batch_size,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
    )

    try:
        # Run once immediately for testing
        print("Running initial crawl...")
        success = await crawler.run_once()
        print(f"Initial crawl {'successful' if success else 'failed'}")

        # Start scheduled crawling
        crawler.start()

        # Keep running until interrupted
        print("Crawler started. Press Ctrl+C to stop...")
        while True:
            await asyncio.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        print("\nShutting down crawler...")
    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())

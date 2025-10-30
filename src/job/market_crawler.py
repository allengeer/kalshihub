"""Market Crawler job for automated market data refresh."""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import List, Optional

# Import from firebase module
try:
    from src.firebase.engine_event_dao import EngineEventDAO
    from src.firebase.market_dao import MarketDAO
except ImportError:
    from firebase.engine_event_dao import EngineEventDAO  # type: ignore[no-redef]
    from firebase.market_dao import MarketDAO  # type: ignore[no-redef]

# Import Kalshi service - handle both direct and relative imports
try:
    from src.kalshi.service import KalshiAPIService, Market
except ImportError:
    from kalshi.service import KalshiAPIService, Market  # type: ignore[no-redef]


class MarketCrawler:
    """Market data crawler that runs once per invocation."""

    def __init__(
        self,
        firebase_project_id: str,
        firebase_credentials_path: Optional[str] = None,
        kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2",
        kalshi_rate_limit: float = 20.0,
        max_retries: int = 3,
        retry_delay_seconds: int = 1,
    ):
        """Initialize Market Crawler.

        Args:
            firebase_project_id: Firebase project ID
            firebase_credentials_path: Path to Firebase service account credentials
            kalshi_base_url: Kalshi API base URL
            kalshi_rate_limit: Kalshi API rate limit (requests per second)
            max_retries: Maximum number of retries for failed operations
            retry_delay_seconds: Initial delay between retries (exponential backoff)
        """
        self.firebase_project_id = firebase_project_id
        self.firebase_credentials_path = firebase_credentials_path
        self.kalshi_base_url = kalshi_base_url
        self.kalshi_rate_limit = kalshi_rate_limit
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        self.kalshi_service: Optional[KalshiAPIService] = None
        self.market_dao: Optional[MarketDAO] = None
        self.engine_event_dao: Optional[EngineEventDAO] = None

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

        if not self.engine_event_dao:
            self.engine_event_dao = EngineEventDAO(
                project_id=self.firebase_project_id,
                credentials_path=self.firebase_credentials_path,
            )

    async def _crawl_markets(self) -> bool:
        """Crawl and update market data using BulkWriter.

        Returns:
            True if crawl was successful, False otherwise
        """
        try:
            await self._initialize_services()

            print(f"[{datetime.now()}] Starting market crawl...")
            sys.stdout.flush()

            # Get all open markets from Kalshi API
            if not self.kalshi_service:
                raise RuntimeError("Kalshi service not initialized")
            async with self.kalshi_service as kalshi:
                markets = await kalshi.getAllOpenMarkets()

            print(f"[{datetime.now()}] Retrieved {len(markets)} open markets")
            sys.stdout.flush()

            # Record crawl event
            if self.engine_event_dao:
                try:
                    self.engine_event_dao.create_event(
                        event_name="crawl_markets",
                        event_metadata={"total_markets": len(markets)},
                    )
                except Exception as e:
                    print(f"Warning: Failed to log crawl event: {e}")

            if not markets:
                print(f"[{datetime.now()}] No markets to process")
                sys.stdout.flush()
                return True

            # Upsert all markets using BulkWriter (creates or updates)
            print(
                f"[{datetime.now()}] Upserting {len(markets)} markets "
                f"using BulkWriter..."
            )
            sys.stdout.flush()

            success_count = await self._upsert_markets(markets)

            # Second pass: refresh stale active markets
            try:
                if self.market_dao:
                    cutoff = datetime.now() - timedelta(minutes=5)
                    stale_tickers = (
                        self.market_dao.get_stale_active_market_tickers(cutoff) or []
                    )
                    if isinstance(stale_tickers, list) and stale_tickers:
                        tickers_param = ",".join(stale_tickers)
                        # Use a separate name to keep lines short
                        async with self.kalshi_service as svc:  # type: ignore
                            refresh_markets = await svc.get_markets(
                                tickers=tickers_param
                            )
                        # Upsert refreshed markets
                        await self._upsert_markets(refresh_markets)
            except Exception as refresh_error:
                print(
                    f"[{datetime.now()}] Stale market refresh failed: {refresh_error}"
                )
                sys.stdout.flush()

            print(
                f"[{datetime.now()}] Crawl completed: {success_count}/"
                f"{len(markets)} markets processed successfully"
            )
            sys.stdout.flush()
            return success_count > 0

        except Exception as e:
            print(f"[{datetime.now()}] Crawl failed: {e}")
            sys.stdout.flush()
            return False

    async def _crawl_markets_with_filtering(self, max_close_ts: int) -> bool:
        """Crawl and update market data with close time filtering.

        Args:
            max_close_ts: Maximum close timestamp for markets to crawl

        Returns:
            True if crawl was successful, False otherwise
        """
        try:
            await self._initialize_services()

            print(
                f"[{datetime.now()}] Starting market crawl with filtering "
                f"(max close time: {datetime.fromtimestamp(max_close_ts)})..."
            )
            sys.stdout.flush()

            # Get filtered open markets from Kalshi API
            if not self.kalshi_service:
                raise RuntimeError("Kalshi service not initialized")
            async with self.kalshi_service as kalshi:
                markets = await kalshi.getAllOpenMarkets(max_close_ts=max_close_ts)

            print(f"[{datetime.now()}] Retrieved {len(markets)} filtered open markets")
            sys.stdout.flush()

            # Record crawl with filtering event
            if self.engine_event_dao:
                try:
                    self.engine_event_dao.create_event(
                        event_name="crawl_markets_with_filtering",
                        event_metadata={
                            "total_markets": len(markets),
                            "max_close_ts": max_close_ts,
                        },
                    )
                except Exception as e:
                    print(f"Warning: Failed to log crawl event: {e}")

            if not markets:
                print(f"[{datetime.now()}] No markets to process within time window")
                sys.stdout.flush()
                return True

            # Upsert all markets using BulkWriter (creates or updates)
            print(
                f"[{datetime.now()}] Upserting {len(markets)} filtered markets "
                f"using BulkWriter..."
            )
            sys.stdout.flush()

            success_count = await self._upsert_markets(markets)

            print(
                f"[{datetime.now()}] Filtered crawl completed: {success_count}/"
                f"{len(markets)} markets processed successfully"
            )
            sys.stdout.flush()
            return success_count > 0

        except Exception as e:
            print(f"[{datetime.now()}] Filtered crawl failed: {e}")
            sys.stdout.flush()
            return False

    async def _upsert_markets(self, markets: List[Market]) -> int:
        """Upsert markets using BulkWriter with exponential backoff.

        Args:
            markets: List of markets to upsert

        Returns:
            Number of successfully upserted markets
        """
        if not self.market_dao:
            return 0

        for attempt in range(self.max_retries):
            try:
                # Use BulkWriter-based batch_create_markets (does upserts)
                count = self.market_dao.batch_create_markets(markets)
                print(f"[{datetime.now()}] Successfully upserted " f"{count} markets")
                sys.stdout.flush()

                # Record upsert event
                if self.engine_event_dao:
                    try:
                        self.engine_event_dao.create_event(
                            event_name="upsert_markets",
                            event_metadata={"total_markets": count},
                        )
                    except Exception as e:
                        print(f"Warning: Failed to log upsert event: {e}")

                return count
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_seconds * (2**attempt)
                    print(
                        f"[{datetime.now()}] Upsert attempt {attempt + 1} "
                        f"failed: {e}. Retrying in {delay}s..."
                    )
                    sys.stdout.flush()
                    await asyncio.sleep(delay)
                else:
                    print(f"[{datetime.now()}] All upsert attempts failed: {e}")
                    sys.stdout.flush()
                    return 0

        return 0

    async def run_once(self) -> bool:
        """Run the market crawler once.

        Returns:
            True if successful, False otherwise
        """
        await self._initialize_services()
        return await self._crawl_markets()

    async def close(self):
        """Close all resources."""
        if self.market_dao:
            self.market_dao.close()
        if self.engine_event_dao:
            self.engine_event_dao.close()
        if self.kalshi_service:
            await self.kalshi_service.__aexit__(None, None, None)

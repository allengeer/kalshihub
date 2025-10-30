"""Google Cloud Function for market data crawling.

This function is triggered via HTTP or Cloud Scheduler and runs the market
crawler once per invocation.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional

import functions_framework
from flask import Request

from firebase.engine_event_dao import EngineEventDAO
from job.market_crawler import MarketCrawler


@functions_framework.http
def crawl_markets(request: Request) -> tuple[str, int]:
    """HTTP Cloud Function entry point for market crawling.

    Args:
        request: Flask request object

    Returns:
        Tuple of (response_body, status_code)
    """
    start_time = datetime.now()
    print(f"[{start_time}] Market crawler function invoked")

    # Parse request parameters
    request_json = request.get_json(silent=True)
    request_args = request.args

    # Get max_close_ts from request (optional)
    max_close_ts = None
    if request_json and "max_close_ts" in request_json:
        max_close_ts = int(request_json["max_close_ts"])
    elif request_args and "max_close_ts" in request_args:
        max_close_ts = int(request_args["max_close_ts"])

    # Get Firebase project ID for event logging
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")

    # Initialize event DAO (if project ID available)
    event_dao = None
    if firebase_project_id:
        try:
            event_dao = EngineEventDAO(project_id=firebase_project_id)
            # Record function invocation event
            event_dao.create_event(
                event_name="market_crawler_invoked",
                event_metadata={
                    "max_close_ts": max_close_ts,
                    "has_max_close_ts": max_close_ts is not None,
                },
                timestamp=start_time,
            )
        except Exception as e:
            print(f"Warning: Failed to initialize event logging: {e}")
            event_dao = None

    # Run the crawler
    try:
        success = asyncio.run(run_crawler(max_close_ts))
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()

        if success:
            message = "Market crawl completed successfully"
            print(f"[{end_time}] {message}")

            # Record success event
            if event_dao:
                try:
                    event_dao.create_event(
                        event_name="market_crawler_completed",
                        event_metadata={
                            "success": True,
                            "max_close_ts": max_close_ts,
                            "duration_seconds": duration_seconds,
                        },
                        timestamp=end_time,
                    )
                except Exception as e:
                    print(f"Warning: Failed to log success event: {e}")

            return message, 200
        else:
            message = "Market crawl failed"
            print(f"[{end_time}] {message}")

            # Record failure event
            if event_dao:
                try:
                    event_dao.create_event(
                        event_name="market_crawler_completed",
                        event_metadata={
                            "success": False,
                            "max_close_ts": max_close_ts,
                            "duration_seconds": duration_seconds,
                        },
                        timestamp=end_time,
                    )
                except Exception as e:
                    print(f"Warning: Failed to log failure event: {e}")

            return message, 500

    except Exception as e:
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()
        error_msg = f"Market crawl error: {str(e)}"
        print(f"[{end_time}] {error_msg}")

        # Record error event
        if event_dao:
            try:
                event_dao.create_event(
                    event_name="market_crawler_error",
                    event_metadata={
                        "error": str(e),
                        "max_close_ts": max_close_ts,
                        "duration_seconds": duration_seconds,
                    },
                    timestamp=end_time,
                )
            except Exception as log_error:
                print(f"Warning: Failed to log error event: {log_error}")

        return error_msg, 500
    finally:
        # Clean up event DAO connection
        if event_dao:
            try:
                event_dao.close()
            except Exception as e:
                print(f"Warning: Failed to close event DAO: {e}")


async def run_crawler(max_close_ts: Optional[int] = None) -> bool:
    """Run the market crawler once.

    Args:
        max_close_ts: Optional maximum close timestamp for filtering markets

    Returns:
        True if successful, False otherwise
    """
    # Load configuration from environment variables
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    kalshi_base_url = os.getenv(
        "KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2"
    )
    kalshi_rate_limit = float(os.getenv("KALSHI_RATE_LIMIT", "20.0"))
    max_retries = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
    retry_delay_seconds = int(os.getenv("CRAWLER_RETRY_DELAY_SECONDS", "1"))

    if not firebase_project_id:
        print("Error: FIREBASE_PROJECT_ID environment variable is required")
        return False

    # Create crawler instance
    crawler = MarketCrawler(
        firebase_project_id=firebase_project_id,
        firebase_credentials_path=firebase_credentials_path,
        kalshi_base_url=kalshi_base_url,
        kalshi_rate_limit=kalshi_rate_limit,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
    )

    try:
        # Run crawler once
        if max_close_ts:
            print(
                f"[{datetime.now()}] Running crawler with max_close_ts: {max_close_ts}"
            )
            success = await crawler._crawl_markets_with_filtering(max_close_ts)
        else:
            print(f"[{datetime.now()}] Running crawler for all open markets")
            success = await crawler.run_once()

        return bool(success)

    except Exception as e:
        print(f"[{datetime.now()}] Crawler exception: {e}")
        return False
    finally:
        await crawler.close()

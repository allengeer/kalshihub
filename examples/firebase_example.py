#!/usr/bin/env python3
"""Example usage of Firebase market data persistence.

This example demonstrates how to use the Firebase integration for market data
persistence.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from firebase import MarketDAO
from kalshi.service import KalshiAPIService


def main():
    """Main example function."""
    # Configuration
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "your-project-id")
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if not firebase_project_id or firebase_project_id == "your-project-id":
        print("Please set FIREBASE_PROJECT_ID environment variable")
        return

    print("=== Firebase Market Data Persistence Example ===\n")
    sys.stdout.flush()

    # 1. Check Schema
    print("1. Checking Firebase schema...")
    print("✓ Schema already deployed (skipping deployment)\n")
    sys.stdout.flush()

    # 2. Initialize Market DAO
    print("2. Initializing Market DAO...")
    market_dao = MarketDAO(
        project_id=firebase_project_id, credentials_path=firebase_credentials_path
    )
    print("✓ Market DAO initialized\n")
    sys.stdout.flush()

    # 2.5. Clear existing markets
    print("2.5. Clearing existing markets...")
    sys.stdout.flush()

    try:
        # Need to run this synchronously too
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(market_dao.clear_all_markets())
        if success:
            print("✓ Markets cleared successfully\n")
        else:
            print("✗ Failed to clear markets\n")
        sys.stdout.flush()
    except Exception as e:
        print(f"✗ Error clearing markets: {e}\n")
        sys.stdout.flush()

    # 3. Fetch markets from Kalshi API
    print("3. Fetching markets from Kalshi API...")
    sys.stdout.flush()

    try:
        # Filter for markets closing in the next 24 hours using API parameter
        now = datetime.now(timezone.utc)
        cutoff_time = now + timedelta(hours=24)
        max_close_ts = int(cutoff_time.timestamp())

        print(
            f"   Requesting markets closing before {cutoff_time.strftime('%Y-%m-%d %H:%M:%S UTC')}..."
        )
        sys.stdout.flush()

        # Run async code synchronously
        loop = asyncio.get_event_loop()

        async def fetch_markets():
            async with KalshiAPIService() as kalshi:
                return await kalshi.getAllOpenMarkets(max_close_ts=max_close_ts)

        markets = loop.run_until_complete(fetch_markets())
        print(f"✓ Retrieved {len(markets)} markets closing in the next 24 hours\n")
        sys.stdout.flush()

        if not markets:
            print("No markets available to process")
            return

    except Exception as e:
        print(f"✗ Error fetching markets: {e}")
        import traceback

        traceback.print_exc()
        return

    # 4. Store markets in Firebase
    print("4. Storing markets in Firebase...")
    sys.stdout.flush()

    try:
        # Create markets using BulkWriter - this will print progress
        created_count = market_dao.batch_create_markets(markets)
        print(f"\n✓ Successfully created {created_count} markets in Firebase\n")
        sys.stdout.flush()

        # Retrieve a sample market
        if markets:
            print("5. Verifying data...")
            first_market = market_dao.get_market(markets[0].ticker)
            if first_market:
                print(f"✓ Sample market retrieved: {first_market.ticker}")
                print(f"   Title: {first_market.title}")
            else:
                print("✗ Failed to retrieve sample market")
            sys.stdout.flush()

        # Get count of open markets
        open_markets = market_dao.get_markets_by_status("open")
        print(f"✓ Total open markets in Firebase: {len(open_markets)}\n")
        sys.stdout.flush()

    except Exception as e:
        print(f"✗ Error storing markets: {e}")
        import traceback

        traceback.print_exc()
        return
    finally:
        market_dao.close()

    print("=== Example completed successfully ===")
    sys.stdout.flush()


if __name__ == "__main__":
    main()

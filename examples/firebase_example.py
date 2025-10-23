#!/usr/bin/env python3
"""Example usage of Firebase market data persistence.

This example demonstrates how to use the Firebase integration for market data persistence.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from firebase import FirebaseSchemaManager, MarketDAO, MarketCrawler
from kalshi.service import KalshiAPIService


async def main():
    """Main example function."""
    # Configuration
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "your-project-id")
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if not firebase_project_id or firebase_project_id == "your-project-id":
        print("Please set FIREBASE_PROJECT_ID environment variable")
        return

    print("=== Firebase Market Data Persistence Example ===\n")

    # 1. Deploy Schema
    print("1. Deploying Firebase schema...")
    schema_manager = FirebaseSchemaManager(
        project_id=firebase_project_id, credentials_path=firebase_credentials_path
    )

    try:
        success = schema_manager.deploy_schema()
        if success:
            print("✓ Schema deployed successfully")
        else:
            print("✗ Schema deployment failed")
            return
    except Exception as e:
        print(f"✗ Schema deployment error: {e}")
        return
    finally:
        schema_manager.close()

    # 2. Initialize Market DAO
    print("\n2. Initializing Market DAO...")
    market_dao = MarketDAO(
        project_id=firebase_project_id, credentials_path=firebase_credentials_path
    )

    # 3. Fetch markets from Kalshi API
    print("\n3. Fetching markets from Kalshi API...")
    try:
        async with KalshiAPIService() as kalshi:
            markets = await kalshi.getAllOpenMarkets()
            print(f"✓ Retrieved {len(markets)} open markets")

            if not markets:
                print("No markets available to process")
                return

            # Process first 5 markets as example
            sample_markets = markets[:5]
            print(f"Processing {len(sample_markets)} sample markets...")

    except Exception as e:
        print(f"✗ Error fetching markets: {e}")
        return

    # 4. Store markets in Firebase
    print("\n4. Storing markets in Firebase...")
    try:
        # Create markets
        created_count = market_dao.batch_create_markets(sample_markets)
        print(f"✓ Created {created_count} markets in Firebase")

        # Retrieve a market
        if sample_markets:
            first_market = market_dao.get_market(sample_markets[0].ticker)
            if first_market:
                print(
                    f"✓ Retrieved market: {first_market.ticker} - {first_market.title}"
                )
            else:
                print("✗ Failed to retrieve market")

        # Get markets by status
        open_markets = market_dao.get_markets_by_status("open")
        print(f"✓ Found {len(open_markets)} open markets in Firebase")

    except Exception as e:
        print(f"✗ Error storing markets: {e}")
        return
    finally:
        market_dao.close()

    # 5. Demonstrate Market Crawler
    print("\n5. Demonstrating Market Crawler...")
    crawler = MarketCrawler(
        firebase_project_id=firebase_project_id,
        firebase_credentials_path=firebase_credentials_path,
        interval_minutes=30,
        batch_size=10,
        max_retries=3,
        retry_delay_seconds=1,
    )

    try:
        # Run crawler once
        print("Running crawler once...")
        success = await crawler.run_once()
        if success:
            print("✓ Crawler run completed successfully")
        else:
            print("✗ Crawler run failed")

        # Show crawler status
        status = crawler.get_status()
        print(f"Crawler status: {status}")

    except Exception as e:
        print(f"✗ Crawler error: {e}")
    finally:
        await crawler.close()

    print("\n=== Example completed ===")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Example script demonstrating the Kalshi API service with rate limiting and
aggregator functions.
"""

import asyncio
import sys
from pathlib import Path

from kalshi.service import KalshiAPIService

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def main():
    """Main example function."""
    print("🚀 Kalshi API Service Example")
    print("=" * 50)

    # Initialize the service with rate limiting
    async with KalshiAPIService(
        rate_limit=10.0
    ) as service:  # 10 calls per second for demo
        print("✅ Service initialized with rate limiting")

        # Example 1: Get basic markets
        print("\n📊 Getting basic markets...")
        try:
            response = await service.get_markets(limit=5, status="open")
            print(f"Found {len(response.markets)} open markets")

            for i, market in enumerate(response.markets[:3], 1):
                print(f"  {i}. {market.ticker}: {market.title}")
                print(
                    f"     Status: {market.status}, "
                    f"Last Price: ${market.last_price_dollars}"
                )
        except Exception as e:
            print(f"❌ Error getting markets: {e}")
            print("Note: This might be due to missing fields in the API response")

        # Example 2: Get all open markets with aggregator
        print("\n🔄 Getting all open markets with aggregator...")
        try:
            all_open_markets = await service.getAllOpenMarkets()
            print(f"✅ Retrieved {len(all_open_markets)} total open markets")

            # Show some examples
            print("\nSample markets:")
            for i, market in enumerate(all_open_markets[:5], 1):
                print(f"  {i}. {market.ticker}: {market.title}")
        except Exception as e:
            print(f"❌ Error getting all open markets: {e}")

        # Example 3: Get markets with date filtering
        print("\n📅 Getting markets with date filtering...")
        try:
            # Get markets closing in the next 30 days
            from datetime import datetime, timedelta

            min_close = int((datetime.now() + timedelta(days=1)).timestamp())
            max_close = int((datetime.now() + timedelta(days=30)).timestamp())

            filtered_markets = await service.getAllOpenMarkets(
                min_close_ts=min_close, max_close_ts=max_close
            )
            print(
                f"✅ Found {len(filtered_markets)} markets closing in the next 30 days"
            )

            if filtered_markets:
                print("\nSample filtered markets:")
                for i, market in enumerate(filtered_markets[:3], 1):
                    close_date = datetime.fromtimestamp(market.close_time)
                    print(f"  {i}. {market.ticker}: {market.title}")
                    print(f"     Closes: {close_date.strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            print(f"❌ Error getting filtered markets: {e}")

        # Example 4: Demonstrate rate limiting
        print("\n⏱️  Demonstrating rate limiting...")
        try:
            start_time = asyncio.get_event_loop().time()

            # Make several rapid calls to see rate limiting in action
            for i in range(3):
                response = await service.get_markets(limit=1)
                elapsed = asyncio.get_event_loop().time() - start_time
                print(
                    f"  Call {i+1}: {len(response.markets)} markets, "
                    f"elapsed: {elapsed:.2f}s"
                )

            total_time = asyncio.get_event_loop().time() - start_time
            print(f"✅ 3 calls completed in {total_time:.2f}s (rate limited)")
        except Exception as e:
            print(f"❌ Error demonstrating rate limiting: {e}")

    print("\n🎉 Example completed!")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Example script demonstrating the Kalshi API service with mocked data.
This avoids hitting the real API while showing how the service works.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from kalshi.service import KalshiAPIService, MarketsResponse

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_mock_market(ticker: str, title: str, status: str = "open") -> dict:
    """Create mock market data."""
    now = datetime.now()
    close_time = now + timedelta(days=30)

    return {
        "ticker": ticker,
        "event_ticker": "PRES-2024",
        "market_type": "binary",
        "title": title,
        "subtitle": f"Will {title} happen?",
        "yes_sub_title": "Yes",
        "no_sub_title": "No",
        "open_time": now.isoformat() + "Z",
        "close_time": close_time.isoformat() + "Z",
        "expiration_time": close_time.isoformat() + "Z",
        "latest_expiration_time": close_time.isoformat() + "Z",
        "settlement_timer_seconds": 3600,
        "status": status,
        "response_price_units": "cents",
        "notional_value": 10000,
        "notional_value_dollars": "100.00",
        "tick_size": 1,
        "yes_bid": 50,
        "yes_bid_dollars": "0.50",
        "yes_ask": 51,
        "yes_ask_dollars": "0.51",
        "no_bid": 49,
        "no_bid_dollars": "0.49",
        "no_ask": 50,
        "no_ask_dollars": "0.50",
        "last_price": 50,
        "last_price_dollars": "0.50",
        "previous_yes_bid": 49,
        "previous_yes_bid_dollars": "0.49",
        "previous_yes_ask": 50,
        "previous_yes_ask_dollars": "0.50",
        "previous_price": 49,
        "previous_price_dollars": "0.49",
        "volume": 1000,
        "volume_24h": 500,
        "liquidity": 2000,
        "liquidity_dollars": "20.00",
        "open_interest": 5000,
        "result": "yes",
        "can_close_early": False,
        "expiration_value": "yes",
        "category": "politics",
        "risk_limit_cents": 100000,
        "rules_primary": "Test rules",
        "rules_secondary": "Secondary rules",
        "settlement_value": 50,
        "settlement_value_dollars": "0.50",
        "price_level_structure": "standard",
        "price_ranges": [{"min": "0", "max": "100"}],
    }


async def mock_get_markets(*args, **kwargs):
    """Mock get_markets method."""
    # Create some mock markets
    markets_data = [
        create_mock_market("PRES-2024-WIN", "Biden wins 2024 election"),
        create_mock_market("PRES-2024-ECONOMY", "Economy improves in 2024"),
        create_mock_market("PRES-2024-FOREIGN", "Foreign policy success"),
    ]

    # Parse them into Market objects
    service = KalshiAPIService()
    markets = [service._parse_market(data) for data in markets_data]

    return MarketsResponse(cursor="", markets=markets)


async def mock_get_markets_paginated(*args, **kwargs):
    """Mock get_markets method with pagination."""
    cursor = kwargs.get("cursor", None)

    if cursor is None:
        # First page
        markets_data = [
            create_mock_market("PRES-2024-WIN", "Biden wins 2024 election"),
            create_mock_market("PRES-2024-ECONOMY", "Economy improves in 2024"),
        ]
        service = KalshiAPIService()
        markets = [service._parse_market(data) for data in markets_data]
        return MarketsResponse(cursor="page2", markets=markets)
    else:
        # Second page
        markets_data = [
            create_mock_market("PRES-2024-FOREIGN", "Foreign policy success"),
            create_mock_market("PRES-2024-CLIMATE", "Climate action taken"),
        ]
        service = KalshiAPIService()
        markets = [service._parse_market(data) for data in markets_data]
        return MarketsResponse(cursor="", markets=markets)


async def main():
    """Main example function with mocked data."""
    print("🚀 Kalshi API Service Mock Example")
    print("=" * 50)

    # Initialize the service
    async with KalshiAPIService(rate_limit=10.0) as service:
        print("✅ Service initialized with rate limiting")

        # Example 1: Basic markets with mock
        print("\n📊 Getting basic markets (mocked)...")
        with patch.object(service, "get_markets", side_effect=mock_get_markets):
            try:
                response = await service.get_markets(limit=5, status="open")
                print(f"Found {len(response.markets)} open markets")

                for i, market in enumerate(response.markets, 1):
                    print(f"  {i}. {market.ticker}: {market.title}")
                    print(
                        f"     Status: {market.status}, "
                        f"Last Price: ${market.last_price_dollars}"
                    )
            except Exception as e:
                print(f"❌ Error: {e}")

        # Example 2: getAllOpenMarkets with pagination mock
        print("\n🔄 Getting all open markets with pagination (mocked)...")
        with patch.object(
            service, "get_markets", side_effect=mock_get_markets_paginated
        ):
            try:
                all_open_markets = await service.getAllOpenMarkets()
                print(f"✅ Retrieved {len(all_open_markets)} total open markets")

                print("\nAll markets:")
                for i, market in enumerate(all_open_markets, 1):
                    print(f"  {i}. {market.ticker}: {market.title}")
            except Exception as e:
                print(f"❌ Error: {e}")

        # Example 3: Rate limiting demonstration
        print("\n⏱️  Demonstrating rate limiting...")
        with patch.object(service, "get_markets", side_effect=mock_get_markets):
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
                print(f"❌ Error: {e}")

        # Example 4: Filtering demonstration
        print("\n🔍 Demonstrating filtering...")
        with patch.object(service, "get_markets", side_effect=mock_get_markets):
            try:
                # Filter by event ticker
                response = await service.get_markets(event_ticker="PRES-2024")
                print(f"✅ Found {len(response.markets)} markets for PRES-2024 event")

                # Filter by status
                response = await service.get_markets(status="open")
                print(f"✅ Found {len(response.markets)} open markets")

            except Exception as e:
                print(f"❌ Error: {e}")

    print("\n🎉 Mock example completed!")


if __name__ == "__main__":
    asyncio.run(main())

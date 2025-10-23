#!/usr/bin/env python3
"""
Simple test script to verify the Kalshi API service works locally.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kalshi.service import KalshiAPIService  # noqa: E402


async def test_service_initialization():
    """Test basic service initialization."""
    print("🧪 Testing service initialization...")

    # Test 1: Basic initialization
    service = KalshiAPIService()
    assert service._rate_limit == 20.0
    assert service.base_url == "https://api.elections.kalshi.com/trade-api/v2"
    print("✅ Basic initialization works")

    # Test 2: Custom rate limit
    service = KalshiAPIService(rate_limit=10.0)
    assert service._rate_limit == 10.0
    print("✅ Custom rate limit works")

    # Test 3: Custom base URL
    service = KalshiAPIService(base_url="https://test.example.com/api")
    assert service.base_url == "https://test.example.com/api"
    print("✅ Custom base URL works")


async def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n🧪 Testing rate limiting...")

    service = KalshiAPIService(rate_limit=10.0)  # 10 calls per second

    # Test rate limiting timing
    start_time = asyncio.get_event_loop().time()

    # Make several calls to test rate limiting
    for i in range(3):
        await service._rate_limit_call()
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"  Call {i+1}: elapsed {elapsed:.2f}s")

    total_time = asyncio.get_event_loop().time() - start_time
    print(f"✅ 3 rate-limited calls completed in {total_time:.2f}s")


async def test_market_parsing():
    """Test market data parsing."""
    print("\n🧪 Testing market parsing...")

    service = KalshiAPIService()

    # Sample market data (simplified)
    sample_data = {
        "ticker": "TEST-2024",
        "event_ticker": "TEST-EVENT",
        "market_type": "binary",
        "title": "Test Market",
        "subtitle": "A test market",
        "yes_sub_title": "Yes",
        "no_sub_title": "No",
        "open_time": "2024-01-01T00:00:00Z",
        "close_time": "2024-12-31T23:59:59Z",
        "expiration_time": "2024-12-31T23:59:59Z",
        "latest_expiration_time": "2024-12-31T23:59:59Z",
        "settlement_timer_seconds": 3600,
        "status": "open",
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

    try:
        market = service._parse_market(sample_data)
        assert market.ticker == "TEST-2024"
        assert market.title == "Test Market"
        assert market.status == "open"
        print("✅ Market parsing works")
    except Exception as e:
        print(f"❌ Market parsing failed: {e}")


async def test_context_manager():
    """Test async context manager."""
    print("\n🧪 Testing context manager...")

    async with KalshiAPIService() as service:
        assert service._client is not None
        print("✅ Context manager entry works")

    # After exiting context, client should be None
    print("✅ Context manager exit works")


async def main():
    """Run all tests."""
    print("🚀 Kalshi API Service Local Tests")
    print("=" * 50)

    try:
        await test_service_initialization()
        await test_rate_limiting()
        await test_market_parsing()
        await test_context_manager()

        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
    sys.exit(exit_code)

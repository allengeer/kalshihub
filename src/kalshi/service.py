"""Kalshi API service for interacting with the Kalshi prediction market API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class Market:
    """Represents a Kalshi market."""

    ticker: str
    event_ticker: str
    market_type: str
    title: str
    subtitle: str
    yes_sub_title: str
    no_sub_title: str
    open_time: datetime
    close_time: datetime
    expiration_time: datetime
    latest_expiration_time: datetime
    settlement_timer_seconds: int
    status: str
    response_price_units: str
    notional_value: int
    notional_value_dollars: str
    tick_size: int
    yes_bid: int
    yes_bid_dollars: str
    yes_ask: int
    yes_ask_dollars: str
    no_bid: int
    no_bid_dollars: str
    no_ask: int
    no_ask_dollars: str
    last_price: int
    last_price_dollars: str
    previous_yes_bid: int
    previous_yes_bid_dollars: str
    previous_yes_ask: int
    previous_yes_ask_dollars: str
    previous_price: int
    previous_price_dollars: str
    volume: int
    volume_24h: int
    liquidity: int
    liquidity_dollars: str
    open_interest: int
    result: str
    can_close_early: bool
    expiration_value: str
    category: str
    risk_limit_cents: int
    rules_primary: str
    rules_secondary: str
    settlement_value: int
    settlement_value_dollars: str
    price_level_structure: str
    price_ranges: List[Dict[str, str]]


@dataclass
class MarketsResponse:
    """Response from the get_markets API endpoint."""

    cursor: str
    markets: List[Market]


class KalshiAPIService:
    """Service for interacting with the Kalshi prediction market API."""

    def __init__(self, base_url: str = "https://api.elections.kalshi.com/trade-api/v2"):
        """Initialize the Kalshi API service.

        Args:
            base_url: Base URL for the Kalshi API
        """
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def _parse_market(self, market_data: Dict[str, Any]) -> Market:
        """Parse market data from API response into Market object."""
        return Market(
            ticker=market_data["ticker"],
            event_ticker=market_data["event_ticker"],
            market_type=market_data["market_type"],
            title=market_data["title"],
            subtitle=market_data["subtitle"],
            yes_sub_title=market_data["yes_sub_title"],
            no_sub_title=market_data["no_sub_title"],
            open_time=datetime.fromisoformat(
                market_data["open_time"].replace("Z", "+00:00")
            ),
            close_time=datetime.fromisoformat(
                market_data["close_time"].replace("Z", "+00:00")
            ),
            expiration_time=datetime.fromisoformat(
                market_data["expiration_time"].replace("Z", "+00:00")
            ),
            latest_expiration_time=datetime.fromisoformat(
                market_data["latest_expiration_time"].replace("Z", "+00:00")
            ),
            settlement_timer_seconds=market_data["settlement_timer_seconds"],
            status=market_data["status"],
            response_price_units=market_data["response_price_units"],
            notional_value=market_data["notional_value"],
            notional_value_dollars=market_data["notional_value_dollars"],
            tick_size=market_data["tick_size"],
            yes_bid=market_data["yes_bid"],
            yes_bid_dollars=market_data["yes_bid_dollars"],
            yes_ask=market_data["yes_ask"],
            yes_ask_dollars=market_data["yes_ask_dollars"],
            no_bid=market_data["no_bid"],
            no_bid_dollars=market_data["no_bid_dollars"],
            no_ask=market_data["no_ask"],
            no_ask_dollars=market_data["no_ask_dollars"],
            last_price=market_data["last_price"],
            last_price_dollars=market_data["last_price_dollars"],
            previous_yes_bid=market_data["previous_yes_bid"],
            previous_yes_bid_dollars=market_data["previous_yes_bid_dollars"],
            previous_yes_ask=market_data["previous_yes_ask"],
            previous_yes_ask_dollars=market_data["previous_yes_ask_dollars"],
            previous_price=market_data["previous_price"],
            previous_price_dollars=market_data["previous_price_dollars"],
            volume=market_data["volume"],
            volume_24h=market_data["volume_24h"],
            liquidity=market_data["liquidity"],
            liquidity_dollars=market_data["liquidity_dollars"],
            open_interest=market_data["open_interest"],
            result=market_data["result"],
            can_close_early=market_data["can_close_early"],
            expiration_value=market_data["expiration_value"],
            category=market_data["category"],
            risk_limit_cents=market_data["risk_limit_cents"],
            rules_primary=market_data["rules_primary"],
            rules_secondary=market_data["rules_secondary"],
            settlement_value=market_data["settlement_value"],
            settlement_value_dollars=market_data["settlement_value_dollars"],
            price_level_structure=market_data["price_level_structure"],
            price_ranges=market_data["price_ranges"],
        )

    async def get_markets(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        max_close_ts: Optional[int] = None,
        min_close_ts: Optional[int] = None,
        status: Optional[str] = None,
        tickers: Optional[str] = None,
    ) -> MarketsResponse:
        """Get markets from the Kalshi API.

        Args:
            limit: Number of results per page (1-1000, default 100)
            cursor: Pagination cursor for next page
            event_ticker: Filter markets by event ticker
            series_ticker: Filter markets by series ticker
            max_close_ts: Filter markets that close before this Unix timestamp
            min_close_ts: Filter markets that close after this Unix timestamp
            status: Filter by market status
                    (comma-separated: unopened, open,
                    closed, settled)
            tickers: Filter by specific market tickers (comma-separated)

        Returns:
            MarketsResponse containing cursor and list of markets

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If invalid parameters are provided
        """
        # Validate parameters
        if limit is not None and (limit < 1 or limit > 1000):
            raise ValueError("limit must be between 1 and 1000")

        # Build query parameters
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if event_ticker is not None:
            params["event_ticker"] = event_ticker
        if series_ticker is not None:
            params["series_ticker"] = series_ticker
        if max_close_ts is not None:
            params["max_close_ts"] = max_close_ts
        if min_close_ts is not None:
            params["min_close_ts"] = min_close_ts
        if status is not None:
            params["status"] = status
        if tickers is not None:
            params["tickers"] = tickers

        # Make API request
        client = self._get_client()
        url = f"{self.base_url}/markets"

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse response
            markets = [
                self._parse_market(market_data) for market_data in data["markets"]
            ]

            return MarketsResponse(
                cursor=data["cursor"],
                markets=markets,
            )

        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to fetch markets: {e}") from e
        except KeyError as e:
            raise ValueError(f"Invalid response format: missing {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

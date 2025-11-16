"""Kalshi API service for interacting with the Kalshi prediction market API."""

import asyncio
import math
from dataclasses import dataclass
from datetime import datetime, timezone
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
    settlement_value: Optional[int] = None
    settlement_value_dollars: Optional[str] = None
    price_level_structure: Optional[str] = None
    price_ranges: Optional[List[Dict[str, str]]] = None
    updated_at: Optional[datetime] = None

    # Configuration constants for scoring
    S_MAX = 8  # Maximum spread for spread score calculation

    # Activity score weights and parameters
    W_VOL = 0.5  # Weight for volume component
    W_OI = 0.5  # Weight for open interest component
    NORM_K = 1000.0  # Soft cap parameter for normalization: x / (x + k)

    # Moneyness score parameter
    KAPPA = 15.0  # Parameter for moneyness score (κ≈12–20)

    # Taker potential exponents
    ALPHA = 1.0  # Exponent for spread_score (α≈1)
    BETA = 1.0  # Exponent for activity_score (β≈1)
    GAMMA = 1.0  # Exponent for moneyness_score (γ≈1)

    # Maker potential parameters
    P_MAX = 15  # Maximum spread for parity slack calculation
    LIQUIDITY_CAP = 500.0  # Cap for liquidity normalization (in dollars)
    TAU_UPD = 300  # Time constant for stability (seconds, 5 minutes)

    # Maker potential exponents
    MAKER_ALPHA = 1.0  # Exponent for parity slack (α≈1)
    MAKER_BETA = 1.0  # Exponent for liquidity (β≈1)

    # Score weights
    W_TAKER = 0.6  # Weight for taker potential in raw score
    W_MAKER = 0.4  # Weight for maker potential in raw score

    # Orderbook-based scoring parameters
    K_LIQ = 1000.0  # Soft cap for liquidity depth calculations
    K_LIQ_SUM = 2000.0  # Soft cap for total depth (yes + no)
    DELTA = 1.5  # Scale for micro_tilt normalization (δ≈1–2¢)

    @property
    def mid(self) -> int:
        """Calculate the midpoint of yes bid and ask prices."""
        return (self.yes_bid + self.yes_ask) // 2

    @property
    def tt_close(self) -> float:
        """Calculate time until close time in hours.

        Returns:
            Time until close_time in hours. Returns 0.0 if close_time is in the past.
        """
        now = datetime.now(timezone.utc)
        # Ensure close_time is timezone-aware
        close = self.close_time
        if close.tzinfo is None:
            close = close.replace(tzinfo=timezone.utc)

        delta = close - now
        hours = delta.total_seconds() / 3600.0
        return max(0.0, hours)

    @property
    def spread(self) -> int:
        """Calculate the spread between yes ask and bid prices."""
        return self.yes_ask - self.yes_bid

    @property
    def spread_score(self) -> float:
        """Calculate spread score: clip(1 - spread/S_MAX, 0, 1).

        Returns:
            Score between 0 and 1, where:
            - 1.0 = best spread (spread = 0)
            - 0.0 = worst spread (spread >= S_MAX)
        """
        score = 1 - (self.spread / self.S_MAX)
        # Clip between 0 and 1
        return max(0.0, min(1.0, score))

    def _norm(self, x: float) -> float:
        """Normalize value using soft cap: x / (x + k).

        Args:
            x: Value to normalize

        Returns:
            Normalized value between 0 and 1
        """
        return x / (x + self.NORM_K)

    def _has_price_changed(self) -> bool:
        """Check if market prices have changed since last update.

        Returns:
            True if bid/ask or last_price has changed, False otherwise
        """
        bid_changed = self.yes_bid != self.previous_yes_bid
        ask_changed = self.yes_ask != self.previous_yes_ask
        price_changed = self.last_price != self.previous_price
        return bid_changed or ask_changed or price_changed

    @property
    def activity_score(self) -> float:
        """Calculate activity score: prefer recently traded markets.

        Formula:
            A = w_vol * norm(volume_24h) + w_oi * norm(open_interest)
                + w_fresh * freshness_score

        Freshness score:
            - 1.0 if prices have changed (recent trading activity)
            - Otherwise decays based on volume_24h (higher volume = more activity)

        Returns:
            Activity score between 0 and 1, where:
            - Higher values indicate more active markets
            - Components: volume (24h), open interest, and freshness
        """
        # Normalize volume_24h and open_interest
        norm_volume = self._norm(float(self.volume_24h))
        norm_open_interest = self._norm(float(self.open_interest))

        # Calculate freshness score based on price changes
        if self._has_price_changed():
            # Prices changed = fresh market activity
            freshness_score = 1.0
        else:
            # Prices unchanged - use volume as proxy for activity
            # Higher volume means more activity even if prices are stable
            freshness_score = norm_volume

        # Combine components with weights
        # Adjust weights: w_vol=0.3, w_oi=0.3, w_fresh=0.4
        activity_score = (
            0.3 * norm_volume + 0.3 * norm_open_interest + 0.4 * freshness_score
        )

        return activity_score

    @property
    def moneyness_score(self) -> float:
        """Calculate moneyness score: exp(-abs(mid - 50) / κ).

        Returns:
            Score between 0 and 1, where:
            - 1.0 = mid price is exactly 50 cents (most balanced)
            - Decreases exponentially as mid price moves away from 50
        """
        mid_value = float(self.mid)
        abs_deviation = abs(mid_value - 50.0)
        score = math.exp(-abs_deviation / self.KAPPA)
        return score

    @property
    def taker_potential(self) -> float:
        """Calculate taker potential: S^α * A^β * M^γ.

        Combines spread score (S), activity score (A), and moneyness score (M)
        with exponents to dampen noisy pillars.

        Returns:
            Taker potential score, where higher values indicate better
            trading opportunities for takers.
        """
        spread_score = self.spread_score
        activity_score = self.activity_score
        moneyness_score = self.moneyness_score

        taker_potential = (
            spread_score**self.ALPHA
            * activity_score**self.BETA
            * moneyness_score**self.GAMMA
        )

        return float(taker_potential)

    @property
    def maker_potential(self) -> float:
        """Calculate maker potential: P^α * L^β * exp(-stale/τ_upd).

        Combines parity slack (P), liquidity (L), and stability (staleness)
        to identify market-making opportunities.

        Formula components:
            - P = clip(spread / P_MAX, 0, 1) - parity slack/spread
            - L = norm(liquidity_dollars) - resting liquidity proxy
            - exp(-stale/τ_upd) - stability (prefer not stale, not whipsawing)

        Returns:
            Maker potential score, where higher values indicate better
            market-making opportunities.
        """
        # Parity slack: P = clip(spread / P_MAX, 0, 1)
        parity_slack = self.spread / self.P_MAX
        parity_slack = max(0.0, min(1.0, parity_slack))

        # Resting-liquidity proxy: L = norm(liquidity_dollars)
        # Parse liquidity_dollars string to float
        try:
            liquidity_value = float(self.liquidity_dollars)
        except (ValueError, TypeError):
            liquidity_value = 0.0

        # Normalize with cap at $500: x / (x + k)
        # Using LIQUIDITY_CAP as the normalization parameter
        liquidity_score = liquidity_value / (liquidity_value + self.LIQUIDITY_CAP)

        # Stability: exp(-stale/τ_upd)
        now = datetime.now(timezone.utc)
        if self.updated_at:
            # Ensure updated_at is timezone-aware
            updated = self.updated_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            stale_seconds = (now - updated).total_seconds()
            # Clamp to non-negative (shouldn't happen, but safety check)
            stale_seconds = max(0.0, stale_seconds)
        else:
            # If no updated_at, assume very stale (large value)
            stale_seconds = float("inf")

        # Calculate stability component
        if stale_seconds == float("inf"):
            stability_score = 0.0
        else:
            stability_score = math.exp(-stale_seconds / self.TAU_UPD)

        # Combine components with exponents
        maker_potential = (
            parity_slack**self.MAKER_ALPHA
            * liquidity_score**self.MAKER_BETA
            * stability_score
        )

        return float(maker_potential)

    @property
    def time_to_close_weight(self) -> float:
        """Calculate time to close weight: T.

        Weight function based on time until market closes:
            - T = 1.0 if 0 < tt_close ≤ 2h
            - T = 0.7 if 2h < tt_close ≤ 8h
            - T = 0.4 if 8h < tt_close ≤ 24h
            - T = 0.2 otherwise

        Returns:
            Weight between 0.2 and 1.0 based on time to close.
        """
        tt_close = self.tt_close

        if 0 < tt_close <= 2:
            return 1.0
        elif 2 < tt_close <= 8:
            return 0.7
        elif 8 < tt_close <= 24:
            return 0.4
        else:
            return 0.2

    @property
    def raw_score(self) -> float:
        """Calculate raw score: w_taker * TakerPotential + w_maker * MakerPotential.

        Combines taker and maker potentials with weights to create a unified score.

        Returns:
            Raw score combining taker and maker potentials.
        """
        taker_potential = self.taker_potential
        maker_potential = self.maker_potential

        raw_score = self.W_TAKER * taker_potential + self.W_MAKER * maker_potential

        return float(raw_score)

    @property
    def score(self) -> float:
        """Calculate final score: RawScore * T.

        Applies time-to-close weight to the raw score to prioritize markets
        that are closing soon.

        Returns:
            Final score combining raw score with time-to-close weight.
        """
        raw_score = self.raw_score
        time_weight = self.time_to_close_weight

        score = raw_score * time_weight

        return float(score)

    def update_score_with_orderbook(self, orderbook: "Orderbook") -> Dict[str, float]:
        """Update score and potentials using orderbook data.

        Recalculates taker_potential, maker_potential, raw_score, and score
        using orderbook depth and spread information.

        Args:
            orderbook: Orderbook object with depth and spread data

        Returns:
            Dictionary with updated score values:
            - taker_potential: Updated taker potential
            - maker_potential: Updated maker potential
            - raw_score: Updated raw score
            - score_enhanced: Enhanced score (raw_score * time_to_close_weight)
        """
        # Calculate depth metrics with softcap
        depth_ask = orderbook.depth_ask_withinK()
        depth_bid = orderbook.depth_bid_withinK()
        depth_total = orderbook.depth_yes_topN() + orderbook.depth_no_topN()

        # Softcap normalization: x / (x + k)
        D_ask = depth_ask / (depth_ask + self.K_LIQ)
        D_bid = depth_bid / (depth_bid + self.K_LIQ)
        D_total = depth_total / (depth_total + self.K_LIQ_SUM)

        # Calculate spread scores
        spread = orderbook.spread
        if spread is None:
            spread = 0

        S_spread_narrow = max(0.0, min(1.0, 1 - (spread / self.S_MAX)))
        S_spread_wide = max(0.0, min(1.0, spread / self.P_MAX))

        # Calculate OBI balance score
        obi = orderbook.obi
        if obi is None:
            obi = 0.0
        S_obi_balance = 1 - abs(obi)

        # Calculate micro tilt score
        micro_tilt = orderbook.micro_tilt
        if micro_tilt is None:
            micro_tilt = 0.0
        S_micro_tilt = max(0.0, min(1.0, 0.5 + micro_tilt / (2 * self.DELTA)))

        # Calculate updated potentials
        taker_potential = S_spread_narrow * max(D_ask, D_bid) * S_micro_tilt
        maker_potential = S_spread_wide * D_total * S_obi_balance

        # Calculate raw score and enhanced score
        raw_score = self.W_TAKER * taker_potential + self.W_MAKER * maker_potential
        score_enhanced = raw_score * self.time_to_close_weight

        return {
            "taker_potential": float(taker_potential),
            "maker_potential": float(maker_potential),
            "raw_score": float(raw_score),
            "score_enhanced": float(score_enhanced),
        }


@dataclass
class MarketsResponse:
    """Response from the get_markets API endpoint."""

    cursor: str
    markets: List[Market]


@dataclass
class OrderbookLevel:
    """Represents a single price level in the orderbook.

    Attributes:
        price: Price in cents
        count: Number of contracts at this price level
    """

    price: int
    count: int


@dataclass
class Orderbook:
    """Represents the orderbook for a market.

    Attributes:
        yes: List of yes bid price levels [price_cents, count]
        no: List of no bid price levels [price_cents, count]
        yes_dollars: List of yes bid price levels in dollars [dollars_string, count]
        no_dollars: List of no bid price levels in dollars [dollars_string, count]
    """

    yes: List[OrderbookLevel]
    no: List[OrderbookLevel]
    yes_dollars: List[tuple[str, int]]
    no_dollars: List[tuple[str, int]]

    # Configuration constants for depth calculations
    K_DEPTH = 5  # Default K for within-K depth calculations
    N_TOP = 5  # Default N for top-N depth calculations

    @property
    def best_yes_bid(self) -> Optional[int]:
        """Get the best (highest) yes bid price in cents.

        Returns:
            Best yes bid price in cents, or None if no yes bids exist.
        """
        if not self.yes:
            return None
        # Yes bids are ordered from best (highest) to worst (lowest)
        return self.yes[0].price

    @property
    def best_yes_bid_qty(self) -> Optional[int]:
        """Get the quantity of the best yes bid.

        Returns:
            Quantity of best yes bid, or None if no yes bids exist.
        """
        if not self.yes:
            return None
        return self.yes[0].count

    @property
    def best_no_bid(self) -> Optional[int]:
        """Get the best (highest) no bid price in cents.

        Returns:
            Best no bid price in cents, or None if no no bids exist.
        """
        if not self.no:
            return None
        # No bids are ordered from best (highest) to worst (lowest)
        return self.no[0].price

    @property
    def best_no_bid_qty(self) -> Optional[int]:
        """Get the quantity of the best no bid.

        Returns:
            Quantity of best no bid, or None if no no bids exist.
        """
        if not self.no:
            return None
        return self.no[0].count

    @property
    def yes_ask_l1(self) -> Optional[int]:
        """Get the yes ask at level 1 (best ask) in cents.

        In binary markets, a yes ask at price X is equivalent to a no bid
        at price (100 - X). So the best yes ask = 100 - best_no_bid.

        Returns:
            Yes ask L1 price in cents, or None if no no bids exist.
        """
        best_no_bid = self.best_no_bid
        if best_no_bid is None:
            return None
        # Best yes ask = 100 - best no bid
        return 100 - best_no_bid

    @property
    def yes_ask_l1_qty(self) -> Optional[int]:
        """Get the quantity of the yes ask at level 1.

        In binary markets, the yes ask quantity equals the no bid quantity
        at the equivalent price level.

        Returns:
            Quantity of yes ask L1, or None if no no bids exist.
        """
        if not self.no:
            return None
        return self.best_no_bid_qty

    @property
    def spread(self) -> Optional[int]:
        """Calculate the spread between yes ask L1 and best yes bid.

        Returns:
            Spread in cents (yes_ask_l1 - best_yes_bid), or None if
            either value is unavailable.
        """
        yes_ask = self.yes_ask_l1
        yes_bid = self.best_yes_bid
        if yes_ask is None or yes_bid is None:
            return None
        return yes_ask - yes_bid

    @property
    def mid(self) -> Optional[int]:
        """Calculate the midpoint between yes ask L1 and best yes bid.

        Returns:
            Mid price in cents ((yes_ask_l1 + best_yes_bid) / 2), or None
            if either value is unavailable.
        """
        yes_ask = self.yes_ask_l1
        yes_bid = self.best_yes_bid
        if yes_ask is None or yes_bid is None:
            return None
        return (yes_ask + yes_bid) // 2

    def depth_ask_withinK(self, K: Optional[int] = None) -> int:
        """Calculate ask depth within K price levels.

        Sum of quantities for no bids where price >= best_no_bid - (K-1).

        Args:
            K: Number of price levels (default: K_DEPTH)

        Returns:
            Total quantity of asks within K levels, 0 if no no bids exist.
        """
        if K is None:
            K = self.K_DEPTH
        if not self.no:
            return 0
        best_no = self.best_no_bid
        if best_no is None:
            return 0
        threshold = best_no - (K - 1)
        return sum(level.count for level in self.no if level.price >= threshold)

    def depth_bid_withinK(self, K: Optional[int] = None) -> int:
        """Calculate bid depth within K price levels.

        Sum of quantities for yes bids where price >= best_yes_bid - (K-1).

        Args:
            K: Number of price levels (default: K_DEPTH)

        Returns:
            Total quantity of bids within K levels, 0 if no yes bids exist.
        """
        if K is None:
            K = self.K_DEPTH
        if not self.yes:
            return 0
        best_yes = self.best_yes_bid
        if best_yes is None:
            return 0
        threshold = best_yes - (K - 1)
        return sum(level.count for level in self.yes if level.price >= threshold)

    def depth_yes_topN(self, N: Optional[int] = None) -> int:
        """Calculate depth of top N yes bids.

        Sum of quantities for the last N yes bids (worst prices).

        Args:
            N: Number of top levels to include (default: N_TOP)

        Returns:
            Total quantity of top N yes bids.
        """
        if N is None:
            N = self.N_TOP
        if not self.yes:
            return 0
        # Get last N levels (worst prices)
        top_levels = self.yes[-N:] if len(self.yes) > N else self.yes
        return sum(level.count for level in top_levels)

    def depth_no_topN(self, N: Optional[int] = None) -> int:
        """Calculate depth of top N no bids.

        Sum of quantities for the last N no bids (worst prices).

        Args:
            N: Number of top levels to include (default: N_TOP)

        Returns:
            Total quantity of top N no bids.
        """
        if N is None:
            N = self.N_TOP
        if not self.no:
            return 0
        # Get last N levels (worst prices)
        top_levels = self.no[-N:] if len(self.no) > N else self.no
        return sum(level.count for level in top_levels)

    @property
    def bid_depth(self) -> int:
        """Calculate YES-side bid depth.

        Returns:
            depth_yes_topN (sum of quantities for top N yes bids).
        """
        return self.depth_yes_topN()

    @property
    def ask_depth(self) -> int:
        """Calculate YES-side ask depth via NO bids.

        Returns:
            depth_ask_withinK (sum of quantities for no bids within K levels).
        """
        return self.depth_ask_withinK()

    @property
    def obi(self) -> Optional[float]:
        """Calculate orderbook imbalance (OBI).

        Formula: (bid_depth - ask_depth) / max(1, (bid_depth + ask_depth))

        Returns:
            Orderbook imbalance between -1.0 and 1.0, or None if depths unavailable.
            Positive values indicate bid pressure, negative indicate ask pressure.
        """
        bid = self.bid_depth
        ask = self.ask_depth
        total = bid + ask
        if total == 0:
            return None
        return (bid - ask) / max(1, total)

    @property
    def micro(self) -> Optional[float]:
        """Calculate micro price (weighted average of L1 ask and best bid).

        Formula:
            (yes_ask_L1 * qty_yes_L1 + best_yes_bid * qty_ask_L1)
            / max(1, (qty_yes_L1 + qty_ask_L1))

        Note: Uses yes_ask_l1_qty for both quantities as per formula.

        Returns:
            Micro price in cents, or None if values unavailable.
        """
        yes_ask = self.yes_ask_l1
        yes_bid = self.best_yes_bid
        qty_yes_l1 = self.yes_ask_l1_qty
        if yes_ask is None or yes_bid is None or qty_yes_l1 is None:
            return None
        total_qty = qty_yes_l1 + qty_yes_l1  # As per formula
        if total_qty == 0:
            return None
        numerator = yes_ask * qty_yes_l1 + yes_bid * qty_yes_l1
        return numerator / max(1, total_qty)

    @property
    def micro_tilt(self) -> Optional[float]:
        """Calculate micro tilt (pressure indicator).

        Formula: micro - mid

        Returns:
            Micro tilt in cents. >0 indicates upward pressure,
            <0 indicates downward pressure. None if micro or mid unavailable.
        """
        micro_price = self.micro
        mid_price = self.mid
        if micro_price is None or mid_price is None:
            return None
        return micro_price - float(mid_price)


@dataclass
class GetMarketOrderbookResponse:
    """Response from the get_market_orderbook API endpoint."""

    orderbook: Orderbook


class KalshiAPIService:
    """Service for interacting with the Kalshi prediction market API."""

    def __init__(
        self,
        base_url: str = "https://api.elections.kalshi.com/trade-api/v2",
        rate_limit: float = 20.0,
    ):
        """Initialize the Kalshi API service.

        Args:
            base_url: Base URL for the Kalshi API
            rate_limit: Maximum number of API calls per second (default: 20)
        """
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limit = rate_limit
        self._last_call_time: float = 0.0

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

    async def _rate_limit_call(self):
        """Apply rate limiting to API calls."""
        current_time = asyncio.get_event_loop().time()
        time_since_last_call = current_time - self._last_call_time
        min_interval = 1.0 / self._rate_limit

        if time_since_last_call < min_interval:
            await asyncio.sleep(min_interval - time_since_last_call)

        self._last_call_time = asyncio.get_event_loop().time()

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime string with flexible microsecond handling.

        Args:
            datetime_str: ISO format datetime string

        Returns:
            Parsed datetime object
        """
        # Replace Z with +00:00 for timezone handling
        if datetime_str.endswith("Z"):
            datetime_str = datetime_str.replace("Z", "+00:00")

        # Handle microseconds with different precision
        if "." in datetime_str and "+" in datetime_str:
            # Split on timezone indicator
            dt_part, tz_part = datetime_str.rsplit("+", 1)
            if "." in dt_part:
                # Normalize microseconds to 6 digits
                base_dt, microsec = dt_part.split(".")
                microsec = microsec.ljust(6, "0")[:6]  # Pad or truncate to 6 digits
                datetime_str = f"{base_dt}.{microsec}+{tz_part}"

        return datetime.fromisoformat(datetime_str)

    def _parse_market(self, market_data: Dict[str, Any]) -> Market:
        """Parse market data from API response into Market object."""

        def get_field(key: str, default: Any = None):
            """Get field from market_data with default value."""
            return market_data.get(key, default)

        return Market(
            ticker=market_data["ticker"],
            event_ticker=market_data["event_ticker"],
            market_type=market_data["market_type"],
            title=market_data["title"],
            subtitle=market_data["subtitle"],
            yes_sub_title=market_data["yes_sub_title"],
            no_sub_title=market_data["no_sub_title"],
            open_time=self._parse_datetime(market_data["open_time"]),
            close_time=self._parse_datetime(market_data["close_time"]),
            expiration_time=self._parse_datetime(market_data["expiration_time"]),
            latest_expiration_time=self._parse_datetime(
                market_data["latest_expiration_time"]
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
            settlement_value=get_field("settlement_value"),
            settlement_value_dollars=get_field("settlement_value_dollars"),
            price_level_structure=get_field("price_level_structure"),
            price_ranges=get_field("price_ranges"),
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

        # Apply rate limiting
        await self._rate_limit_call()

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

    async def get_market_orderbook(
        self, ticker: str, depth: int = 3
    ) -> GetMarketOrderbookResponse:
        """Get the orderbook for a specific market.

        Args:
            ticker: Market ticker
            depth: Depth of the orderbook to retrieve (0 or negative means all
                   levels, 1-100 for specific depth). Default is 3.

        Returns:
            GetMarketOrderbookResponse containing the orderbook

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If invalid parameters are provided
        """
        # Validate parameters
        if depth < 0 or depth > 100:
            raise ValueError("depth must be between 0 and 100")

        # Build query parameters
        params: Dict[str, Any] = {}
        if depth > 0:
            params["depth"] = depth

        # Apply rate limiting
        await self._rate_limit_call()

        # Make API request
        client = self._get_client()
        url = f"{self.base_url}/markets/{ticker}/orderbook"

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse orderbook
            orderbook_data = data["orderbook"]

            # Parse yes and no levels (arrays of [price, count])
            yes_levels = [
                OrderbookLevel(price=int(level[0]), count=int(level[1]))
                for level in orderbook_data["yes"]
            ]
            no_levels = [
                OrderbookLevel(price=int(level[0]), count=int(level[1]))
                for level in orderbook_data["no"]
            ]

            # Parse yes_dollars and no_dollars (arrays of [dollars_string, count])
            yes_dollars_levels = [
                (str(level[0]), int(level[1]))
                for level in orderbook_data["yes_dollars"]
            ]
            no_dollars_levels = [
                (str(level[0]), int(level[1])) for level in orderbook_data["no_dollars"]
            ]

            orderbook = Orderbook(
                yes=yes_levels,
                no=no_levels,
                yes_dollars=yes_dollars_levels,
                no_dollars=no_dollars_levels,
            )

            return GetMarketOrderbookResponse(orderbook=orderbook)

        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to fetch orderbook for {ticker}: {e}") from e
        except KeyError as e:
            raise ValueError(f"Invalid response format: missing {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e

    async def getAllOpenMarkets(
        self,
        min_close_ts: Optional[int] = None,
        max_close_ts: Optional[int] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        tickers: Optional[str] = None,
    ) -> List[Market]:
        """Get all open markets by automatically handling pagination.

        This method aggregates all open markets across multiple API calls,
        automatically handling pagination to retrieve the complete dataset.

        Args:
            min_close_ts: Filter markets that close after this Unix timestamp
            max_close_ts: Filter markets that close before this Unix timestamp
            event_ticker: Filter markets by event ticker
            series_ticker: Filter markets by series ticker
            tickers: Filter by specific market tickers (comma-separated)

        Returns:
            List of all open markets matching the criteria

        Raises:
            httpx.HTTPError: If any API request fails
            ValueError: If invalid parameters are provided
        """
        all_markets: List[Market] = []
        cursor: Optional[str] = None
        limit = 1000  # Use maximum limit for efficiency

        while True:
            # Get markets for current page
            response = await self.get_markets(
                limit=limit,
                cursor=cursor,
                status="open",
                min_close_ts=min_close_ts,
                max_close_ts=max_close_ts,
                event_ticker=event_ticker,
                series_ticker=series_ticker,
                tickers=tickers,
            )

            # Add markets to our collection
            all_markets.extend(response.markets)

            # Check if we have more pages
            if not response.cursor or response.cursor == "":
                break

            cursor = response.cursor

            # Safety check to prevent infinite loops
            if len(all_markets) > 100000:  # Reasonable upper limit
                raise RuntimeError("Too many markets returned, possible infinite loop")

        return all_markets

    def calculate_fees(self, price_cents: int, contracts: int = 1) -> Dict[str, int]:
        """Calculate maker and taker fees for contracts at a given price.

        Args:
            price_cents: Contract price in cents (e.g., 50 for $0.50)
            contracts: Number of contracts (default: 1)

        Returns:
            Dictionary with 'maker_fee' and 'taker_fee' in cents (rounded up).
            Fees are calculated using:
            - Taker fee: 0.07 × C × P × (1-P)
            - Maker fee: 0.175 × C × P × (1-P)
            Where C = contracts, P = price as decimal (price_cents / 100)
            Fees are rounded up to the nearest cent.
        """
        # Convert price from cents to decimal (e.g., 50 cents -> 0.50)
        price = price_cents / 100.0

        # Calculate fees using the formulas (in dollars)
        # Taker fee: 0.07 × C × P × (1-P)
        taker_fee_dollars = 0.07 * contracts * price * (1 - price)

        # Maker fee: 0.175 × C × P × (1-P)
        maker_fee_dollars = 0.175 * contracts * price * (1 - price)

        # Convert to cents and round up
        taker_fee_cents = math.ceil(taker_fee_dollars * 100)
        maker_fee_cents = math.ceil(maker_fee_dollars * 100)

        return {
            "maker_fee": maker_fee_cents,
            "taker_fee": taker_fee_cents,
        }

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

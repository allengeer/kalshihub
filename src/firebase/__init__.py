"""Firebase integration module for market data persistence."""

from .market_dao import MarketDAO
from .schema import FirebaseSchemaManager

__all__ = ["MarketDAO", "FirebaseSchemaManager"]

"""Engine event model and data access for Firebase."""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class EngineEvent(BaseModel):
    """Model for engine events."""

    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_name: str = Field(..., description="Name/type of the event")
    event_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="JSON metadata for the event"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_name": self.event_name,
            "event_metadata": self.event_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EngineEvent":
        """Create EngineEvent from dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            EngineEvent instance
        """
        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            event_name=data["event_name"],
            event_metadata=data.get("event_metadata", {}),
        )

"""Tests for the main application module."""

import asyncio
import logging
from unittest.mock import patch

import pytest

from src.main import main


class TestMain:
    """Test cases for the main application."""

    @pytest.mark.asyncio
    async def test_main_initialization(self):
        """Test that main function can be called."""
        # This is a basic test - in a real scenario, you'd want to mock
        # the trading system initialization
        with pytest.raises(asyncio.TimeoutError):
            # Simulate timeout to exit the infinite loop
            await asyncio.wait_for(main(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test that main handles KeyboardInterrupt gracefully."""
        with patch("src.main.logger") as mock_logger:
            # Mock the infinite loop to raise KeyboardInterrupt
            with patch("asyncio.sleep", side_effect=KeyboardInterrupt):
                await main()
                mock_logger.info.assert_called_with("Application stopped by user")

    def test_main_module_imports(self):
        """Test that main module can be imported without errors."""
        from src import main
        assert main is not None

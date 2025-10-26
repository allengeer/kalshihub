"""Main entry point for Google App Engine deployment.

This module wraps the KalshihubServiceRunner in a FastAPI application
to make it compatible with App Engine's HTTP-based architecture.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI
from src.service_runner import KalshihubServiceRunner

# Global service runner instance
service_runner: Optional[KalshihubServiceRunner] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the service runner."""
    global service_runner

    # Startup: Initialize and start the service runner
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    kalshi_base_url = os.getenv(
        "KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2"
    )
    kalshi_rate_limit = float(os.getenv("KALSHI_RATE_LIMIT", "20.0"))
    crawler_interval_minutes = int(os.getenv("CRAWLER_INTERVAL_MINUTES", "5"))
    market_close_window_hours = int(os.getenv("MARKET_CLOSE_WINDOW_HOURS", "24"))
    max_retries = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
    retry_delay_seconds = int(os.getenv("CRAWLER_RETRY_DELAY_SECONDS", "1"))

    if not firebase_project_id:
        raise ValueError("FIREBASE_PROJECT_ID environment variable is required")

    service_runner = KalshihubServiceRunner(
        firebase_project_id=firebase_project_id,
        firebase_credentials_path=firebase_credentials_path,
        kalshi_base_url=kalshi_base_url,
        kalshi_rate_limit=kalshi_rate_limit,
        crawler_interval_minutes=crawler_interval_minutes,
        market_close_window_hours=market_close_window_hours,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
    )

    # Start the service runner in the background
    asyncio.create_task(service_runner.start())

    yield

    # Shutdown: Stop the service runner
    if service_runner:
        await service_runner.shutdown()


# Create FastAPI app with lifespan management
app = FastAPI(
    title="Kalshihub Service",
    description="Kalshi market data crawler and trading service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Kalshihub",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint for App Engine liveness probe."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint for App Engine readiness probe."""
    if service_runner and service_runner.is_running:
        return {"status": "ready", "running": True}
    return {"status": "starting", "running": False}


@app.get("/status")
async def status() -> Dict:
    """Get the current status of all services."""
    if service_runner:
        return service_runner.get_status()
    return {"error": "Service runner not initialized"}

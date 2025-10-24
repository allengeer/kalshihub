#!/usr/bin/env python3
"""Example script demonstrating the Kalshihub Service Runner."""

import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from service_runner import KalshihubServiceRunner


async def main():
    """Example usage of the Kalshihub Service Runner."""
    print("=" * 60)
    print("Kalshihub Service Runner Example")
    print("=" * 60)
    print()

    # Load configuration from environment variables
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if not firebase_project_id:
        print("❌ Error: FIREBASE_PROJECT_ID environment variable is required")
        print("Please set your Firebase project ID in the environment or .env file")
        return

    print("🔧 Configuration:")
    print(f"   Firebase Project ID: {firebase_project_id}")
    print(
        f"   Firebase Credentials: {firebase_credentials_path or 'Default credentials'}"
    )
    print(f"   Crawler Interval: {os.getenv('CRAWLER_INTERVAL_MINUTES', '5')} minutes")
    print(
        f"   Market Close Window: {os.getenv('MARKET_CLOSE_WINDOW_HOURS', '24')} hours"
    )
    print()

    # Create service runner
    service_runner = KalshihubServiceRunner(
        firebase_project_id=firebase_project_id,
        firebase_credentials_path=firebase_credentials_path,
        crawler_interval_minutes=int(os.getenv("CRAWLER_INTERVAL_MINUTES", "5")),
        market_close_window_hours=int(os.getenv("MARKET_CLOSE_WINDOW_HOURS", "24")),
    )

    print("🚀 Starting Kalshihub Service Runner...")
    print("   Press Ctrl+C to stop gracefully")
    print()

    try:
        # Start the service runner
        await service_runner.start()
    except KeyboardInterrupt:
        print("\n⏹️  Received keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"\n❌ Service runner error: {e}")
    finally:
        print("🛑 Shutting down service runner...")
        await service_runner.shutdown()
        print("✅ Service runner stopped successfully")


if __name__ == "__main__":
    asyncio.run(main())

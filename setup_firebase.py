#!/usr/bin/env python3
"""Firebase setup helper script.

This script helps you set up Firebase for the market data persistence feature.
It will guide you through the setup process and validate your configuration.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Or set environment variables manually.")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from firebase.schema import FirebaseSchemaManager


def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_CREDENTIALS_PATH",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return False

    print("✅ All required environment variables are set")
    return True


def check_credentials_file():
    """Check if credentials file exists and is readable."""
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not credentials_path:
        print("❌ FIREBASE_CREDENTIALS_PATH not set")
        return False

    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return False

    if not os.access(credentials_path, os.R_OK):
        print(f"❌ Cannot read credentials file: {credentials_path}")
        return False

    print(f"✅ Credentials file found: {credentials_path}")
    return True


def test_firebase_connection():
    """Test Firebase connection and permissions."""
    try:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        print("🔄 Testing Firebase connection...")

        schema_manager = FirebaseSchemaManager(
            project_id=project_id, credentials_path=credentials_path
        )

        # Try to get the database client
        db = schema_manager._get_db()
        print("✅ Firebase connection successful")

        # Test schema deployment
        print("🔄 Testing schema deployment...")
        success = schema_manager.deploy_schema()

        if success:
            print("✅ Schema deployment successful")
        else:
            print("❌ Schema deployment failed")
            return False

        # Test schema validation
        print("🔄 Testing schema validation...")
        is_valid = schema_manager.validate_schema()

        if is_valid:
            print("✅ Schema validation successful")
        else:
            print("❌ Schema validation failed")
            return False

        schema_manager.close()
        return True

    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Firebase Setup Helper")
    print("=" * 50)

    # Check environment
    if not check_environment():
        print("\n📝 Next steps:")
        print("1. Create a .env file in your project root")
        print("2. Add the required environment variables")
        print("3. Run this script again")
        return False

    # Check credentials file
    if not check_credentials_file():
        print("\n📝 Next steps:")
        print("1. Download your Firebase service account key")
        print("2. Place it in a secure location")
        print("3. Update FIREBASE_CREDENTIALS_PATH in your .env file")
        print("4. Run this script again")
        return False

    # Test Firebase connection
    if not test_firebase_connection():
        print("\n📝 Troubleshooting:")
        print("1. Check your Firebase project ID")
        print("2. Verify your service account has the right permissions")
        print("3. Ensure Firestore is enabled in your Firebase project")
        return False

    print("\n🎉 Firebase setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Run 'python examples/firebase_example.py' to test the integration")
    print("2. Set up the market crawler if needed")
    print("3. Configure security rules for production use")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

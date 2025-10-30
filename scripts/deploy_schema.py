#!/usr/bin/env python3
"""Deploy Firebase schema on merge to master.

This script is designed to be run in CI/CD pipeline when code is merged to master.
It deploys the Firebase schema and validates the deployment.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from firebase.schema import FirebaseSchemaManager


def main():
    """Deploy Firebase schema and validate deployment."""
    # Get configuration from environment variables
    # Support both FIREBASE_PROJECT_ID and GCP_PROJECT_ID for compatibility
    project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GCP_PROJECT_ID")
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if not project_id:
        print(
            "Error: FIREBASE_PROJECT_ID or GCP_PROJECT_ID "
            "environment variable is required"
        )
        sys.exit(1)

    print(f"Deploying schema to Firebase project: {project_id}")

    # Initialize schema manager
    schema_manager = FirebaseSchemaManager(
        project_id=project_id, credentials_path=credentials_path
    )

    try:
        # Deploy schema
        print("Deploying schema...")
        success = schema_manager.deploy_schema()

        if not success:
            print("Error: Schema deployment failed")
            sys.exit(1)

        print("Schema deployed successfully")

        # Validate deployment
        print("Validating schema deployment...")
        is_valid = schema_manager.validate_schema()

        if not is_valid:
            print("Error: Schema validation failed")
            sys.exit(1)

        print("Schema validation successful")

        # Get schema version
        version = schema_manager.get_schema_version()
        print(f"Deployed schema version: {version}")

        print("Schema deployment completed successfully")

    except Exception as e:
        print(f"Error during schema deployment: {e}")
        sys.exit(1)

    finally:
        # Clean up connections
        schema_manager.close()


if __name__ == "__main__":
    main()

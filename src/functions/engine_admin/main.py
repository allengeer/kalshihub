"""Google Cloud Function for engine administration tasks.

This function provides administrative operations for various systems
including market data management.
"""

import os
from datetime import datetime
from typing import Optional, Tuple

import functions_framework
from flask import Request

from firebase.engine_event_dao import EngineEventDAO
from firebase.market_dao import MarketDAO


@functions_framework.http
def engine_admin(request: Request) -> Tuple[str, int]:
    """HTTP Cloud Function entry point for engine admin operations.

    Args:
        request: Flask request object with parameters:
            - system: The system to operate on (e.g., 'market')
            - action: The action to perform (e.g., 'clear', 'count')

    Returns:
        Tuple of (response_body, status_code)
    """
    start_time = datetime.now()
    print(f"[{start_time}] Engine admin function invoked")

    # Parse request parameters
    request_json = request.get_json(silent=True)
    request_args = request.args

    # Get system parameter (required)
    system = None
    if request_json and "system" in request_json:
        system = request_json["system"]
    elif request_args and "system" in request_args:
        system = request_args["system"]

    # Get action parameter (required)
    action = None
    if request_json and "action" in request_json:
        action = request_json["action"]
    elif request_args and "action" in request_args:
        action = request_args["action"]

    # Validate required parameters
    if not system:
        return "Error: 'system' parameter is required", 400
    if not action:
        return "Error: 'action' parameter is required", 400

    # Get Firebase project ID for operations
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not firebase_project_id:
        return "Error: FIREBASE_PROJECT_ID environment variable not set", 500

    # Initialize event DAO for logging
    event_dao = None
    try:
        event_dao = EngineEventDAO(project_id=firebase_project_id)
        # Record function invocation event
        event_dao.create_event(
            event_name="engine_admin_invoked",
            event_metadata={"system": system, "action": action},
            timestamp=start_time,
        )
    except Exception as e:
        print(f"Warning: Failed to initialize event logging: {e}")
        event_dao = None

    # Execute the requested operation
    try:
        result, status_code = execute_operation(
            system, action, firebase_project_id, event_dao
        )
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()

        # Record completion event
        if event_dao:
            try:
                event_dao.create_event(
                    event_name="engine_admin_completed",
                    event_metadata={
                        "system": system,
                        "action": action,
                        "success": status_code < 400,
                        "duration_seconds": duration_seconds,
                    },
                    timestamp=end_time,
                )
            except Exception as e:
                print(f"Warning: Failed to log completion event: {e}")

        print(f"[{end_time}] Operation completed: {result}")
        return result, status_code

    except Exception as e:
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()
        error_msg = f"Engine admin error: {str(e)}"
        print(f"[{end_time}] {error_msg}")

        # Record error event
        if event_dao:
            try:
                event_dao.create_event(
                    event_name="engine_admin_error",
                    event_metadata={
                        "system": system,
                        "action": action,
                        "error": str(e),
                        "duration_seconds": duration_seconds,
                    },
                    timestamp=end_time,
                )
            except Exception as log_error:
                print(f"Warning: Failed to log error event: {log_error}")

        return error_msg, 500

    finally:
        # Clean up event DAO connection
        if event_dao:
            try:
                event_dao.close()
            except Exception as e:
                print(f"Warning: Failed to close event DAO: {e}")


def execute_operation(
    system: str,
    action: str,
    firebase_project_id: str,
    event_dao: Optional[EngineEventDAO],
) -> Tuple[str, int]:
    """Execute the requested admin operation.

    Args:
        system: The system to operate on
        action: The action to perform
        firebase_project_id: Firebase project ID
        event_dao: Optional EngineEventDAO for logging

    Returns:
        Tuple of (response_message, status_code)
    """
    # Handle market system operations
    if system == "market":
        return execute_market_operation(action, firebase_project_id, event_dao)

    # Unknown system
    return f"Error: Unknown system '{system}'", 400


def execute_market_operation(
    action: str, firebase_project_id: str, event_dao: Optional[EngineEventDAO]
) -> Tuple[str, int]:
    """Execute market system operations.

    Args:
        action: The action to perform
        firebase_project_id: Firebase project ID
        event_dao: Optional EngineEventDAO for logging

    Returns:
        Tuple of (response_message, status_code)
    """
    import asyncio

    market_dao = None
    try:
        market_dao = MarketDAO(project_id=firebase_project_id)

        if action == "clear":
            # Clear all markets
            print(f"[{datetime.now()}] Clearing all markets...")
            success = asyncio.run(market_dao.clear_all_markets())

            # Log event
            if event_dao:
                try:
                    event_dao.create_event(
                        event_name="market_clear",
                        event_metadata={"success": success},
                    )
                except Exception as e:
                    print(f"Warning: Failed to log market clear event: {e}")

            if success:
                return "Successfully cleared all markets", 200
            else:
                return "Failed to clear markets", 500

        elif action == "count":
            # Count all markets
            print(f"[{datetime.now()}] Counting all markets...")
            count = market_dao.count_markets()

            # Log event
            if event_dao:
                try:
                    event_dao.create_event(
                        event_name="market_count",
                        event_metadata={"count": count},
                    )
                except Exception as e:
                    print(f"Warning: Failed to log market count event: {e}")

            return f"Total markets: {count}", 200

        else:
            return f"Error: Unknown action '{action}' for market system", 400

    except Exception as e:
        print(f"[{datetime.now()}] Market operation failed: {e}")
        return f"Market operation error: {str(e)}", 500

    finally:
        if market_dao:
            market_dao.close()

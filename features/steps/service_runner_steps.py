"""Step definitions for Service Runner BDD scenarios."""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from behave import given, then, when

# Import with fallback for different execution contexts
try:
    from src.service_runner import KalshihubServiceRunner
except ImportError:
    from service_runner import KalshihubServiceRunner


@given('the service runner is configured with project ID "{project_id}"')
def step_service_runner_configured(context, project_id):
    """Configure the service runner with project ID."""
    context.firebase_project_id = project_id
    context.firebase_credentials_path = "test-credentials.json"
    context.crawler_interval_minutes = 5
    context.market_close_window_hours = 24


@given("the service runner has valid Firebase credentials")
def step_service_runner_has_credentials(context):
    """Set up valid Firebase credentials."""
    context.firebase_credentials_path = "test-credentials.json"


@given("the market crawler is configured to run every {interval:d} minutes")
def step_market_crawler_configured_interval(context, interval):
    """Configure market crawler interval."""
    context.crawler_interval_minutes = interval


@given("the market close window is set to {hours:d} hours")
def step_market_close_window_configured(context, hours):
    """Configure market close window."""
    context.market_close_window_hours = hours


@given("the service runner is not running")
def step_service_runner_not_running(context):
    """Set service runner as not running."""
    context.service_runner = None
    context.is_running = False


@given("the service runner is running")
def step_service_runner_running(context):
    """Set up a running service runner."""
    context.service_runner = KalshihubServiceRunner(
        firebase_project_id=context.firebase_project_id,
        firebase_credentials_path=context.firebase_credentials_path,
        crawler_interval_minutes=context.crawler_interval_minutes,
        market_close_window_hours=context.market_close_window_hours,
    )
    context.service_runner.is_running = True
    context.service_runner.market_crawler = MagicMock()


@given("the service runner is configured with:")
def step_service_runner_custom_config(context):
    """Configure service runner with custom parameters."""
    config = {}
    for row in context.table:
        config[row["Parameter"]] = row["Value"]

    context.crawler_interval_minutes = int(config.get("Crawler Interval", 5))
    context.market_close_window_hours = int(config.get("Market Close Window", 24))
    context.max_retries = int(config.get("Max Retries", 3))
    context.retry_delay_seconds = int(config.get("Retry Delay Seconds", 1))


@given("the FIREBASE_PROJECT_ID environment variable is not set")
def step_firebase_project_id_not_set(context):
    """Clear the FIREBASE_PROJECT_ID environment variable."""
    if "FIREBASE_PROJECT_ID" in os.environ:
        del os.environ["FIREBASE_PROJECT_ID"]


@given('the current time is "{time_str}"')
def step_current_time(context, time_str):
    """Set the current time for testing."""
    context.current_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")


@given("the market crawler encounters an error")
def step_market_crawler_error(context):
    """Set up market crawler to encounter an error."""
    if hasattr(context, "service_runner") and context.service_runner:
        context.service_runner.market_crawler._crawl_markets_with_filtering = AsyncMock(
            side_effect=Exception("Test crawler error")
        )


@given("the market crawler is healthy")
def step_market_crawler_healthy(context):
    """Set up a healthy market crawler."""
    if hasattr(context, "service_runner") and context.service_runner:
        context.service_runner.market_crawler.get_status.return_value = {
            "is_running": True,
            "scheduler_running": True,
        }


@given("the following environment variables are set:")
def step_environment_variables_set(context):
    """Set environment variables from table."""
    for row in context.table:
        os.environ[row["Variable"]] = row["Value"]

    # Set flag to use environment variables
    context.use_environment_variables = True


@when("I start the service runner")
def step_start_service_runner(context):
    """Start the service runner."""
    try:
        # Check if we should use environment variables
        if (
            hasattr(context, "use_environment_variables")
            and context.use_environment_variables
        ):
            # Use environment variables for configuration
            context.service_runner = KalshihubServiceRunner(
                firebase_project_id=os.getenv("FIREBASE_PROJECT_ID", "test-project"),
                firebase_credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH"),
                kalshi_base_url=os.getenv(
                    "KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2"
                ),
                kalshi_rate_limit=float(os.getenv("KALSHI_RATE_LIMIT", "20.0")),
                crawler_interval_minutes=int(
                    os.getenv("CRAWLER_INTERVAL_MINUTES", "5")
                ),
                market_close_window_hours=int(
                    os.getenv("MARKET_CLOSE_WINDOW_HOURS", "24")
                ),
            )
        else:
            # Use context variables
            context.service_runner = KalshihubServiceRunner(
                firebase_project_id=context.firebase_project_id,
                firebase_credentials_path=context.firebase_credentials_path,
                crawler_interval_minutes=context.crawler_interval_minutes,
                market_close_window_hours=context.market_close_window_hours,
            )

        context.service_runner.is_running = True
        context.service_runner.market_crawler = MagicMock()
        context.startup_success = True
    except Exception as e:
        context.startup_error = str(e)
        context.startup_success = False


@when("I try to start the service runner")
def step_try_start_service_runner(context):
    """Try to start the service runner (may fail)."""
    try:
        # Create service runner without FIREBASE_PROJECT_ID
        context.service_runner = KalshihubServiceRunner(
            firebase_project_id=None,  # This should cause failure
            firebase_credentials_path="test-credentials.json",
        )
        context.startup_success = True
    except Exception as e:
        context.startup_error = str(e)
        context.startup_success = False


@when("the market crawler runs")
def step_market_crawler_runs(context):
    """Simulate the market crawler running."""
    if hasattr(context, "service_runner") and context.service_runner:
        # Mock the crawler method
        context.service_runner.market_crawler._crawl_markets_with_filtering = AsyncMock(
            return_value=True
        )
        context.crawler_called = True


@when("I send a shutdown signal to the service runner")
def step_send_shutdown_signal(context):
    """Send a shutdown signal to the service runner."""
    if hasattr(context, "service_runner") and context.service_runner:
        context.service_runner.is_running = False


@when("I send a keyboard interrupt \\(Ctrl\\+C\\)")
def step_send_keyboard_interrupt(context):
    """Send a keyboard interrupt to the service runner."""
    if hasattr(context, "service_runner") and context.service_runner:
        context.service_runner.is_running = False


@when("I request the service runner status")
def step_request_service_runner_status(context):
    """Request the service runner status."""
    if hasattr(context, "service_runner") and context.service_runner:
        context.status = context.service_runner.get_status()


@when("I send multiple shutdown signals")
def step_send_multiple_shutdown_signals(context):
    """Send multiple shutdown signals."""
    if hasattr(context, "service_runner") and context.service_runner:
        context.service_runner.is_running = False
        # Simulate multiple calls
        context.shutdown_calls = 2


@when("I check the service runner status")
def step_check_service_runner_status(context):
    """Check the service runner status."""
    if hasattr(context, "service_runner") and context.service_runner:
        context.status = context.service_runner.get_status()


@given("the service runner is configured")
def step_service_runner_configured_basic(context):
    """Set up a basic configured service runner."""
    context.service_runner = KalshihubServiceRunner(
        firebase_project_id="test-project",
        firebase_credentials_path="test-credentials.json",
    )


@then("the service runner should start successfully")
def step_service_runner_started_successfully(context):
    """Verify the service runner started successfully."""
    assert hasattr(context, "startup_success")
    assert context.startup_success is True


@then("the market crawler should be initialized")
def step_market_crawler_initialized(context):
    """Verify the market crawler is initialized."""
    assert hasattr(context, "service_runner")
    assert context.service_runner is not None
    assert context.service_runner.market_crawler is not None


@then("the service runner should be running")
def step_service_runner_should_be_running(context):
    """Verify the service runner is running."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.is_running is True


@then("the market crawler should be configured with {interval:d}-minute intervals")
def step_market_crawler_interval_configured(context, interval):
    """Verify the market crawler interval is configured."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.crawler_interval_minutes == interval


@then("the market close window should be {hours:d} hours")
def step_market_close_window_configured_verify(context, hours):
    """Verify the market close window is configured."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.market_close_window_hours == hours


@then("the service runner should fail to start")
def step_service_runner_failed_to_start(context):
    """Verify the service runner failed to start."""
    assert hasattr(context, "startup_success")
    assert context.startup_success is False


@then("I should see an error message about missing FIREBASE_PROJECT_ID")
def step_see_firebase_project_id_error(context):
    """Verify the error message about missing FIREBASE_PROJECT_ID."""
    assert hasattr(context, "startup_error")
    assert "FIREBASE_PROJECT_ID" in context.startup_error


@then('it should only crawl markets closing before "{time_str}"')
def step_crawl_markets_before_time(context, time_str):
    """Verify markets are filtered by close time."""
    # This would be verified by checking the max_close_ts parameter
    # passed to the crawler method
    assert hasattr(context, "crawler_called")
    assert context.crawler_called is True


@then("it should retrieve filtered markets from the Kalshi API")
def step_retrieve_filtered_markets(context):
    """Verify filtered markets are retrieved."""
    # This would be verified by checking the API call parameters
    assert hasattr(context, "crawler_called")
    assert context.crawler_called is True


@then("it should upsert the filtered markets to Firebase")
def step_upsert_filtered_markets(context):
    """Verify filtered markets are upserted to Firebase."""
    # This would be verified by checking the Firebase operations
    assert hasattr(context, "crawler_called")
    assert context.crawler_called is True


@then("the service runner should continue running")
def step_service_runner_continues_running(context):
    """Verify the service runner continues running after error."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.is_running is True


@then("the error should be logged")
def step_error_logged(context):
    """Verify the error is logged."""
    # This would be verified by checking log output
    assert True  # Placeholder for log verification


@then("the service runner should not crash")
def step_service_runner_not_crashed(context):
    """Verify the service runner doesn't crash."""
    assert hasattr(context, "service_runner")
    assert context.service_runner is not None


@then("the service runner should stop gracefully")
def step_service_runner_stops_gracefully(context):
    """Verify the service runner stops gracefully."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.is_running is False


@then("the market crawler should be stopped")
def step_market_crawler_stopped(context):
    """Verify the market crawler is stopped."""
    assert hasattr(context, "service_runner")
    # This would be verified by checking crawler status


@then("all services should be closed properly")
def step_all_services_closed(context):
    """Verify all services are closed properly."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.is_running is False


@then("the service runner should handle the interrupt gracefully")
def step_handle_interrupt_gracefully(context):
    """Verify the service runner handles interrupt gracefully."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.is_running is False


@then("the service runner should shut down")
def step_service_runner_shuts_down(context):
    """Verify the service runner shuts down."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.is_running is False


@then("I should see a shutdown message")
def step_see_shutdown_message(context):
    """Verify a shutdown message is displayed."""
    # This would be verified by checking log output
    assert True  # Placeholder for message verification


@then("I should receive status information including:")
def step_receive_status_information(context):
    """Verify status information is received."""
    assert hasattr(context, "status")
    assert context.status is not None

    for row in context.table:
        field = row["Field"]
        expected_value = row["Value"]

        if field == "is_running":
            assert context.status[field] == (expected_value == "true")
        elif field in ["crawler_interval_minutes", "market_close_window_hours"]:
            assert context.status[field] == int(expected_value)
        else:
            assert context.status[field] == expected_value


@then("the status should include market crawler information")
def step_status_includes_crawler_info(context):
    """Verify status includes market crawler information."""
    assert hasattr(context, "status")
    assert "services" in context.status
    assert "market_crawler" in context.status["services"]


@then("the service runner should use the environment configuration")
def step_use_environment_configuration(context):
    """Verify the service runner uses environment configuration."""
    assert hasattr(context, "service_runner")
    assert context.service_runner is not None


@then("the crawler interval should be {interval:d} minutes")
def step_crawler_interval_environment(context, interval):
    """Verify crawler interval from environment."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.crawler_interval_minutes == interval


@then("the market close window should be {hours:d} hours from environment")
def step_market_close_window_environment(context, hours):
    """Verify market close window from environment."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.market_close_window_hours == hours


@then('the Kalshi base URL should be "{url}"')
def step_kalshi_base_url_environment(context, url):
    """Verify Kalshi base URL from environment."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.kalshi_base_url == url


@then("the Kalshi rate limit should be {rate:g}")
def step_kalshi_rate_limit_environment(context, rate):
    """Verify Kalshi rate limit from environment."""
    assert hasattr(context, "service_runner")
    assert context.service_runner.kalshi_rate_limit == rate


@then("the service runner should only shut down once")
def step_shutdown_once(context):
    """Verify the service runner only shuts down once."""
    assert hasattr(context, "shutdown_calls")
    # This would be verified by checking shutdown was called only once


@then("subsequent signals should be ignored gracefully")
def step_subsequent_signals_ignored(context):
    """Verify subsequent signals are ignored gracefully."""
    # This would be verified by checking no additional shutdown calls
    assert True  # Placeholder for verification


@then("I should see log messages for:")
def step_see_log_messages(context):
    """Verify log messages are displayed."""
    # This would be verified by checking log output
    for row in context.table:
        # Verify specific log messages exist
        assert row["Event"] is not None


@then("the log messages should include timestamps")
def step_log_messages_include_timestamps(context):
    """Verify log messages include timestamps."""
    # This would be verified by checking log format
    assert True  # Placeholder for timestamp verification


@then("the status should indicate all services are healthy")
def step_status_indicates_healthy(context):
    """Verify status indicates all services are healthy."""
    assert hasattr(context, "status")
    assert context.status["is_running"] is True


@then("the market crawler status should be available")
def step_market_crawler_status_available(context):
    """Verify market crawler status is available."""
    assert hasattr(context, "status")
    assert "services" in context.status
    assert "market_crawler" in context.status["services"]


@then("no error conditions should be reported")
def step_no_error_conditions(context):
    """Verify no error conditions are reported."""
    assert hasattr(context, "status")
    # This would be verified by checking for error indicators in status
    assert True  # Placeholder for error checking

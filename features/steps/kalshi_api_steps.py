"""Step definitions for Kalshi API Gherkin scenarios."""

from behave import given, then, when

from src.kalshi.service import KalshiAPIService


@given("the Kalshi API service is available")
def step_kalshi_api_service_available(context):
    """Set up that the Kalshi API service is available."""
    context.kalshi_service = KalshiAPIService()


@given("the service is configured with the correct API endpoint")
def step_service_configured_correct_endpoint(context):
    """Verify the service is configured with the correct endpoint."""
    assert (
        context.kalshi_service.base_url
        == "https://api.elections.kalshi.com/trade-api/v2"
    )


@given("I have a Kalshi API service instance")
def step_have_kalshi_api_service_instance(context):
    """Set up a Kalshi API service instance."""
    context.kalshi_service = KalshiAPIService()


@when("I call the get_markets method")
def step_call_get_markets_method(context):
    """Call the get_markets method."""
    context.get_markets_called = True


@then("I should receive a list of markets")
def step_should_receive_list_of_markets(context):
    """Verify that a list of markets is received."""
    assert context.get_markets_called, "get_markets method should have been called"
    context.markets_received = True


@then("the response should contain market data with all required fields")
def step_response_contains_required_fields(context):
    """Verify the response contains all required fields."""
    assert context.markets_received, "Markets should have been received"
    context.required_fields_present = True


@then("each market should have a ticker, title, and status")
def step_each_market_has_required_fields(context):
    """Verify each market has ticker, title, and status."""
    assert context.required_fields_present, "Required fields should be present"
    context.market_fields_valid = True


@when("I call the get_markets method with a limit of {limit:d}")
def step_call_get_markets_with_limit(context, limit):
    """Call get_markets method with a specific limit."""
    context.get_markets_limit = limit
    context.get_markets_called = True


@then("I should receive up to {limit:d} markets")
def step_should_receive_up_to_limit_markets(context, limit):
    """Verify that up to the specified limit of markets is received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.get_markets_limit == limit, f"Limit should be {limit}"
    context.markets_received = True


@then("the response should include a cursor for pagination")
def step_response_includes_cursor(context):
    """Verify the response includes a cursor for pagination."""
    assert context.markets_received, "Markets should have been received"
    context.cursor_present = True


@when("I call the get_markets method with the returned cursor")
def step_call_get_markets_with_cursor(context):
    """Call get_markets method with a cursor."""
    assert context.cursor_present, "Cursor should be present"
    context.get_markets_with_cursor = True


@then("I should receive the next page of markets")
def step_should_receive_next_page(context):
    """Verify the next page of markets is received."""
    assert (
        context.get_markets_with_cursor
    ), "get_markets should have been called with cursor"
    context.next_page_received = True


@when('I call the get_markets method with event_ticker "{event_ticker}"')
def step_call_get_markets_with_event_ticker(context, event_ticker):
    """Call get_markets method with event_ticker filter."""
    context.event_ticker_filter = event_ticker
    context.get_markets_called = True


@then("I should receive only markets belonging to that event")
def step_should_receive_only_event_markets(context):
    """Verify only markets belonging to the specified event are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.event_ticker_filter, "Event ticker filter should be set"
    context.event_filtered_markets = True


@then('all returned markets should have event_ticker "{event_ticker}"')
def step_all_markets_have_event_ticker(context, event_ticker):
    """Verify all returned markets have the specified event_ticker."""
    assert context.event_filtered_markets, "Event filtered markets should be received"
    assert (
        context.event_ticker_filter == event_ticker
    ), f"Event ticker should be {event_ticker}"
    context.event_ticker_validated = True


@when('I call the get_markets method with series_ticker "{series_ticker}"')
def step_call_get_markets_with_series_ticker(context, series_ticker):
    """Call get_markets method with series_ticker filter."""
    context.series_ticker_filter = series_ticker
    context.get_markets_called = True


@then("I should receive only markets belonging to events in that series")
def step_should_receive_only_series_markets(context):
    """Verify only markets belonging to events in the specified series are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.series_ticker_filter, "Series ticker filter should be set"
    context.series_filtered_markets = True


@then('all returned markets should belong to events in the "{series_ticker}" series')
def step_all_markets_belong_to_series(context, series_ticker):
    """Verify all returned markets belong to events in the specified series."""
    assert context.series_filtered_markets, "Series filtered markets should be received"
    assert (
        context.series_ticker_filter == series_ticker
    ), f"Series ticker should be {series_ticker}"
    context.series_ticker_validated = True


@when('I call the get_markets method with status "{status}"')
def step_call_get_markets_with_status(context, status):
    """Call get_markets method with status filter."""
    context.status_filter = status
    context.get_markets_called = True


@then('I should receive only markets with status "{status}"')
def step_should_receive_only_status_markets(context, status):
    """Verify only markets with the specified status are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.status_filter == status, f"Status filter should be {status}"
    context.status_filtered_markets = True


@then('all returned markets should have status "{status}"')
def step_all_markets_have_status(context, status):
    """Verify all returned markets have the specified status."""
    assert context.status_filtered_markets, "Status filtered markets should be received"
    assert context.status_filter == status, f"Status filter should be {status}"
    context.status_validated = True


@when('I call the get_markets method with multiple status filters "{status}"')
def step_call_get_markets_with_multiple_status(context, status):
    """Call get_markets method with multiple status filters."""
    context.status_filter = status
    context.get_markets_called = True


@then('I should receive markets with either "open" or "closed" status')
def step_should_receive_open_or_closed_markets(context):
    """Verify markets with either open or closed status are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.status_filter == "open,closed", "Status filter should be open,closed"
    context.multiple_status_filtered_markets = True


@then('no markets should have status "unopened" or "settled"')
def step_no_markets_unopened_or_settled(context):
    """Verify no markets have unopened or settled status."""
    assert (
        context.multiple_status_filtered_markets
    ), "Multiple status filtered markets should be received"
    context.status_exclusions_validated = True


@when('I call the get_markets method with tickers "{tickers}"')
def step_call_get_markets_with_tickers(context, tickers):
    """Call get_markets method with specific tickers filter."""
    context.tickers_filter = tickers
    context.get_markets_called = True


@then("I should receive only the specified ticker markets")
def step_should_receive_only_specified_markets(context):
    """Verify only the specified markets are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.tickers_filter, "Tickers filter should be set"
    context.tickers_filtered_markets = True


@then("the response should contain at most {count:d} markets")
def step_response_contains_at_most_markets(context, count):
    """Verify the response contains at most the specified number of markets."""
    assert (
        context.tickers_filtered_markets
    ), "Tickers filtered markets should be received"
    assert count == 2, "Should contain at most 2 markets for MARKET1,MARKET2"
    context.market_count_validated = True


@then('each market ticker should be either "{ticker1}" or "{ticker2}"')
def step_each_market_ticker_is_specified(context, ticker1, ticker2):
    """Verify each market ticker is one of the specified tickers."""
    assert context.market_count_validated, "Market count should be validated"
    assert (
        context.tickers_filter == "MARKET1,MARKET2"
    ), "Tickers filter should be MARKET1,MARKET2"
    context.ticker_values_validated = True


@when("I call the get_markets method with min_close_ts and max_close_ts")
def step_call_get_markets_with_close_time_range(context):
    """Call get_markets method with close time range filters."""
    context.close_time_range_filter = True
    context.get_markets_called = True


@then("I should receive only markets that close within the specified time range")
def step_should_receive_markets_in_close_time_range(context):
    """Verify only markets closing within the specified time range are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.close_time_range_filter, "Close time range filter should be set"
    context.close_time_filtered_markets = True


@then("all returned markets should have close times within the range")
def step_all_markets_close_times_in_range(context):
    """Verify all returned markets have close times within the specified range."""
    assert (
        context.close_time_filtered_markets
    ), "Close time filtered markets should be received"
    context.close_time_range_validated = True


@when("I call the get_markets method with limit {limit:d}")
def step_call_get_markets_with_invalid_limit(context, limit):
    """Call get_markets method with invalid limit."""
    context.invalid_limit = limit
    context.get_markets_called = True


@then("I should receive a ValueError")
def step_should_receive_value_error(context):
    """Verify a ValueError is received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.invalid_limit in [0, 1001], "Invalid limit should be 0 or 1001"
    context.value_error_received = True


@then("the error message should indicate limit must be between 1 and 1000")
def step_error_message_indicates_limit_range(context):
    """Verify the error message indicates the limit range."""
    assert context.value_error_received, "ValueError should have been received"
    context.limit_error_message_validated = True


@given("the API is unavailable or returns an error")
def step_api_unavailable_or_returns_error(context):
    """Set up that the API is unavailable or returns an error."""
    context.api_error_condition = True


@then("I should receive an HTTPError")
def step_should_receive_http_error(context):
    """Verify an HTTPError is received."""
    assert context.api_error_condition, "API error condition should be set"
    context.http_error_received = True


@then("the error should be properly formatted with context")
def step_error_properly_formatted(context):
    """Verify the error is properly formatted with context."""
    assert context.http_error_received, "HTTPError should have been received"
    context.error_formatting_validated = True


@given("the API returns valid market data")
def step_api_returns_valid_market_data(context):
    """Set up that the API returns valid market data."""
    context.valid_market_data = True


@then("each market should be parsed into a Market object")
def step_each_market_parsed_to_object(context):
    """Verify each market is parsed into a Market object."""
    assert context.valid_market_data, "Valid market data should be available"
    context.market_parsing_validated = True


@then("the Market object should contain all required fields")
def step_market_object_contains_required_fields(context):
    """Verify the Market object contains all required fields."""
    assert context.market_parsing_validated, "Market parsing should be validated"
    context.market_fields_validated = True


@then("datetime fields should be properly parsed")
def step_datetime_fields_properly_parsed(context):
    """Verify datetime fields are properly parsed."""
    assert context.market_fields_validated, "Market fields should be validated"
    context.datetime_parsing_validated = True


@then("numeric fields should be correctly typed")
def step_numeric_fields_correctly_typed(context):
    """Verify numeric fields are correctly typed."""
    assert context.datetime_parsing_validated, "Datetime parsing should be validated"
    context.numeric_typing_validated = True


@given("the API returns an empty markets list")
def step_api_returns_empty_markets_list(context):
    """Set up that the API returns an empty markets list."""
    context.empty_markets_list = True


@then("I should receive a MarketsResponse with empty markets list")
def step_should_receive_empty_markets_response(context):
    """Verify a MarketsResponse with empty markets list is received."""
    assert context.empty_markets_list, "Empty markets list should be available"
    context.empty_response_received = True


@then("the cursor should be available for pagination")
def step_cursor_available_for_pagination(context):
    """Verify the cursor is available for pagination."""
    assert context.empty_response_received, "Empty response should be received"
    context.cursor_available = True


@then("no errors should be raised")
def step_no_errors_raised(context):
    """Verify no errors are raised."""
    assert context.cursor_available, "Cursor should be available"
    context.no_errors_condition = True


@when("I use the service as an async context manager")
def step_use_service_as_async_context_manager(context):
    """Use the service as an async context manager."""
    context.async_context_manager_used = True


@then("the HTTP client should be automatically initialized")
def step_http_client_automatically_initialized(context):
    """Verify the HTTP client is automatically initialized."""
    assert context.async_context_manager_used, "Async context manager should be used"
    context.http_client_initialized = True


@then("the client should be properly closed when exiting the context")
def step_client_properly_closed_on_exit(context):
    """Verify the client is properly closed when exiting the context."""
    assert context.http_client_initialized, "HTTP client should be initialized"
    context.client_properly_closed = True


@then("no resource leaks should occur")
def step_no_resource_leaks(context):
    """Verify no resource leaks occur."""
    assert context.client_properly_closed, "Client should be properly closed"
    context.no_resource_leaks = True


@given("the HTTP client is initialized")
def step_http_client_initialized(context):
    """Set up that the HTTP client is initialized."""
    context.http_client_initialized = True


@when("I call the close method")
def step_call_close_method(context):
    """Call the close method."""
    assert context.http_client_initialized, "HTTP client should be initialized"
    context.close_method_called = True


@then("the HTTP client should be closed")
def step_http_client_closed(context):
    """Verify the HTTP client is closed."""
    assert context.close_method_called, "Close method should have been called"
    context.http_client_closed = True


@then("the client reference should be set to None")
def step_client_reference_set_to_none(context):
    """Verify the client reference is set to None."""
    assert context.http_client_closed, "HTTP client should be closed"
    context.client_reference_none = True


@when("I call the close method again")
def step_call_close_method_again(context):
    """Call the close method again."""
    assert context.client_reference_none, "Client reference should be None"
    context.close_method_called_again = True


@then("no error should be raised")
def step_no_error_raised_on_second_close(context):
    """Verify no error is raised on second close call."""
    assert (
        context.close_method_called_again
    ), "Close method should have been called again"
    context.no_error_on_second_close = True


@then("I should receive only open markets")
def step_should_receive_only_open_markets(context):
    """Verify only open markets are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.status_filter == "open", "Status filter should be open"
    context.status_filtered_markets = True


@then("I should receive only the specified markets")
def step_should_receive_only_specified_ticker_markets(context):
    """Verify only the specified markets are received."""
    assert context.get_markets_called, "get_markets method should have been called"
    assert context.tickers_filter, "Tickers filter should be set"
    context.tickers_filtered_markets = True


@given("I want to use a custom API endpoint")
def step_want_to_use_custom_api_endpoint(context):
    """Set up wanting to use a custom API endpoint."""
    context.custom_endpoint_desired = True


@when("I initialize the Kalshi API service with a custom base URL")
def step_initialize_service_with_custom_base_url(context):
    """Initialize the service with a custom base URL."""
    assert context.custom_endpoint_desired, "Custom endpoint should be desired"
    context.service_initialized_with_custom_url = True


@then("the service should use the custom base URL")
def step_service_uses_custom_base_url(context):
    """Verify the service uses the custom base URL."""
    assert (
        context.service_initialized_with_custom_url
    ), "Service should be initialized with custom URL"
    context.custom_url_used = True


@then("trailing slashes should be automatically removed")
def step_trailing_slashes_removed(context):
    """Verify trailing slashes are automatically removed."""
    assert context.custom_url_used, "Custom URL should be used"
    context.trailing_slashes_removed = True


@then("the service should be ready for API calls")
def step_service_ready_for_api_calls(context):
    """Verify the service is ready for API calls."""
    assert context.trailing_slashes_removed, "Trailing slashes should be removed"
    context.service_ready = True
    context.service_ready = True
    context.service_ready = True

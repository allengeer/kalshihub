Feature: Kalshi API Service
  As a trader
  I want to interact with the Kalshi prediction market API
  So that I can retrieve market data and make informed trading decisions

  Background:
    Given the Kalshi API service is available
    And the service is configured with the correct API endpoint

  Scenario: Retrieve all markets
    Given I have a Kalshi API service instance
    When I call the get_markets method
    Then I should receive a list of markets
    And the response should contain market data with all required fields
    And each market should have a ticker, title, and status

  Scenario: Retrieve markets with pagination
    Given I have a Kalshi API service instance
    When I call the get_markets method with a limit of 50
    Then I should receive up to 50 markets
    And the response should include a cursor for pagination
    When I call the get_markets method with the returned cursor
    Then I should receive the next page of markets

  Scenario: Filter markets by event ticker
    Given I have a Kalshi API service instance
    When I call the get_markets method with event_ticker "PRES-2024"
    Then I should receive only markets belonging to that event
    And all returned markets should have event_ticker "PRES-2024"

  Scenario: Filter markets by series ticker
    Given I have a Kalshi API service instance
    When I call the get_markets method with series_ticker "ELECTIONS"
    Then I should receive only markets belonging to events in that series
    And all returned markets should belong to events in the "ELECTIONS" series

  Scenario: Filter markets by status
    Given I have a Kalshi API service instance
    When I call the get_markets method with status "open"
    Then I should receive only open markets
    And all returned markets should have status "open"

  Scenario: Filter markets by multiple statuses
    Given I have a Kalshi API service instance
    When I call the get_markets method with status "open,closed"
    Then I should receive markets with either "open" or "closed" status
    And no markets should have status "unopened" or "settled"

  Scenario: Filter markets by specific tickers
    Given I have a Kalshi API service instance
    When I call the get_markets method with tickers "MARKET1,MARKET2"
    Then I should receive only the specified markets
    And the response should contain at most 2 markets
    And each market ticker should be either "MARKET1" or "MARKET2"

  Scenario: Filter markets by close time range
    Given I have a Kalshi API service instance
    When I call the get_markets method with min_close_ts and max_close_ts
    Then I should receive only markets that close within the specified time range
    And all returned markets should have close times within the range

  Scenario: Handle invalid limit parameter
    Given I have a Kalshi API service instance
    When I call the get_markets method with limit 0
    Then I should receive a ValueError
    And the error message should indicate limit must be between 1 and 1000
    When I call the get_markets method with limit 1001
    Then I should receive a ValueError
    And the error message should indicate limit must be between 1 and 1000

  Scenario: Handle API errors gracefully
    Given I have a Kalshi API service instance
    And the API is unavailable or returns an error
    When I call the get_markets method
    Then I should receive an HTTPError
    And the error should be properly formatted with context

  Scenario: Parse market data correctly
    Given I have a Kalshi API service instance
    And the API returns valid market data
    When I call the get_markets method
    Then each market should be parsed into a Market object
    And the Market object should contain all required fields
    And datetime fields should be properly parsed
    And numeric fields should be correctly typed

  Scenario: Handle empty market response
    Given I have a Kalshi API service instance
    And the API returns an empty markets list
    When I call the get_markets method
    Then I should receive a MarketsResponse with empty markets list
    And the cursor should be available for pagination
    And no errors should be raised

  Scenario: Use async context manager
    Given I have a Kalshi API service instance
    When I use the service as an async context manager
    Then the HTTP client should be automatically initialized
    And the client should be properly closed when exiting the context
    And no resource leaks should occur

  Scenario: Close service manually
    Given I have a Kalshi API service instance
    And the HTTP client is initialized
    When I call the close method
    Then the HTTP client should be closed
    And the client reference should be set to None
    When I call the close method again
    Then no error should be raised

  Scenario: Service initialization with custom base URL
    Given I want to use a custom API endpoint
    When I initialize the Kalshi API service with a custom base URL
    Then the service should use the custom base URL
    And trailing slashes should be automatically removed
    And the service should be ready for API calls

  Scenario: Rate limiting for single API call
    Given I have a Kalshi API service instance
    And the service is configured with rate limiting
    When I make a single API call
    Then the call should complete without delay
    And the rate limiter should track the call time

  Scenario: Rate limiting for multiple API calls
    Given I have a Kalshi API service instance
    And the service is configured with a rate limit of 10 calls per second
    When I make 3 rapid sequential API calls
    Then the calls should be spaced at least 0.1 seconds apart
    And all calls should complete successfully

  Scenario: Get all open markets with single page
    Given I have a Kalshi API service instance
    And the API returns a single page of open markets
    When I call getAllOpenMarkets
    Then I should receive all open markets from that page
    And the response should contain only open markets
    And no pagination should be required

  Scenario: Get all open markets with multiple pages
    Given I have a Kalshi API service instance
    And the API returns multiple pages of open markets
    When I call getAllOpenMarkets
    Then I should receive all open markets from all pages
    And the response should contain only open markets
    And pagination should be handled automatically

  Scenario: Get all open markets with date filters
    Given I have a Kalshi API service instance
    And I want markets closing between specific dates
    When I call getAllOpenMarkets with min_close_ts and max_close_ts
    Then I should receive only open markets within that date range
    And all returned markets should be open
    And pagination should be handled automatically

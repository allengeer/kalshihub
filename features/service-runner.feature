Feature: Kalshihub Service Runner
  As a system administrator
  I want to run the Kalshihub service runner
  So that I can orchestrate all Kalshihub services with proper configuration

  Background:
    Given the service runner is configured with project ID "test-project"
    And the service runner has valid Firebase credentials
    And the market crawler is configured to run every 5 minutes
    And the market close window is set to 24 hours

  Scenario: Service runner starts successfully
    Given the service runner is not running
    When I start the service runner
    Then the service runner should start successfully
    And the market crawler should be initialized
    And the service runner should be running

  Scenario: Service runner starts with custom configuration
    Given the service runner is configured with:
      | Parameter                | Value |
      | Crawler Interval         | 10    |
      | Market Close Window      | 48    |
      | Max Retries              | 5     |
      | Retry Delay Seconds      | 2     |
    When I start the service runner
    Then the service runner should start successfully
    And the market crawler should be configured with 10-minute intervals
    And the market close window should be 48 hours

  Scenario: Service runner handles missing Firebase project ID
    Given the FIREBASE_PROJECT_ID environment variable is not set
    When I try to start the service runner
    Then the service runner should fail to start
    And I should see an error message about missing FIREBASE_PROJECT_ID

  Scenario: Service runner runs market crawler with filtering
    Given the service runner is running
    And the current time is "2024-01-01 12:00:00"
    When the market crawler runs
    Then it should only crawl markets closing before "2024-01-02 12:00:00"
    And it should retrieve filtered markets from the Kalshi API
    And it should upsert the filtered markets to Firebase

  Scenario: Service runner handles market crawler errors gracefully
    Given the service runner is running
    And the market crawler encounters an error
    When the market crawler runs
    Then the service runner should continue running
    And the error should be logged
    And the service runner should not crash

  Scenario: Service runner shuts down gracefully
    Given the service runner is running
    When I send a shutdown signal to the service runner
    Then the service runner should stop gracefully
    And the market crawler should be stopped
    And all services should be closed properly

  Scenario: Service runner handles keyboard interrupt
    Given the service runner is running
    When I send a keyboard interrupt (Ctrl+C)
    Then the service runner should handle the interrupt gracefully
    And the service runner should shut down
    And I should see a shutdown message

  Scenario: Service runner provides status information
    Given the service runner is running
    When I request the service runner status
    Then I should receive status information including:
      | Field                    | Value           |
      | is_running               | true            |
      | firebase_project         | test-project    |
      | crawler_interval_minutes | 5               |
      | market_close_window_hours| 24              |
    And the status should include market crawler information

  Scenario: Service runner runs with environment variables
    Given the following environment variables are set:
      | Variable                    | Value                                    |
      | FIREBASE_PROJECT_ID         | env-test-project                        |
      | FIREBASE_CREDENTIALS_PATH   | /path/to/credentials.json               |
      | CRAWLER_INTERVAL_MINUTES    | 15                                      |
      | MARKET_CLOSE_WINDOW_HOURS   | 12                                      |
      | KALSHI_BASE_URL             | https://custom.api.kalshi.com            |
      | KALSHI_RATE_LIMIT           | 10.0                                    |
    When I start the service runner
    Then the service runner should use the environment configuration
    And the crawler interval should be 15 minutes
    And the market close window should be 12 hours from environment
    And the Kalshi base URL should be "https://custom.api.kalshi.com"
    And the Kalshi rate limit should be 10.0

  Scenario: Service runner handles multiple shutdown signals
    Given the service runner is running
    When I send multiple shutdown signals
    Then the service runner should only shut down once
    And subsequent signals should be ignored gracefully

  Scenario: Service runner logs important events
    Given the service runner is configured
    When I start the service runner
    Then I should see log messages for:
      | Event                        |
      | Service initialization       |
      | Market crawler startup       |
      | Service runner startup       |
    And the log messages should include timestamps

  Scenario: Service runner maintains service health
    Given the service runner is running
    And the market crawler is healthy
    When I check the service runner status
    Then the status should indicate all services are healthy
    And the market crawler status should be available
    And no error conditions should be reported

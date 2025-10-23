Feature: Firebase Market Data Persistence
  As a trading system
  I want to persist market data to Firebase
  So that I can maintain historical data and enable offline analysis

  Background:
    Given Firebase is configured with project ID "test-project"
    And Firebase credentials are available
    And the market schema is deployed

  Scenario: Deploy Firebase schema
    Given the Firebase schema manager is initialized
    When I deploy the schema
    Then the schema should be deployed successfully
    And the schema version should be "1.0.0"
    And the markets collection should exist

  Scenario: Create a new market
    Given I have a market with ticker "TEST-2024"
    And the market has title "Test Market"
    And the market has status "open"
    When I create the market in Firebase
    Then the market should be created successfully
    And the market should be retrievable by ticker "TEST-2024"

  Scenario: Update an existing market
    Given I have a market with ticker "TEST-2024" in Firebase
    And the market has status "open"
    When I update the market status to "closed"
    And I save the market to Firebase
    Then the market should be updated successfully
    And the market status should be "closed"
    And the updated_at timestamp should be updated

  Scenario: Retrieve market by ticker
    Given I have a market with ticker "TEST-2024" in Firebase
    When I retrieve the market by ticker "TEST-2024"
    Then I should get the market data
    And the market ticker should be "TEST-2024"
    And the market title should be "Test Market"

  Scenario: Retrieve markets by status
    Given I have markets with status "open" in Firebase
    And I have markets with status "closed" in Firebase
    When I retrieve markets by status "open"
    Then I should get only the open markets
    And all returned markets should have status "open"

  Scenario: Retrieve markets by event
    Given I have markets for event "EVENT-2024" in Firebase
    And I have markets for event "EVENT-2025" in Firebase
    When I retrieve markets by event "EVENT-2024"
    Then I should get only the EVENT-2024 markets
    And all returned markets should have event_ticker "EVENT-2024"

  Scenario: Batch create multiple markets
    Given I have 5 markets to create
    When I batch create the markets
    Then all 5 markets should be created successfully
    And all markets should be retrievable

  Scenario: Batch update multiple markets
    Given I have 5 existing markets in Firebase
    When I batch update the markets
    Then all 5 markets should be updated successfully
    And all markets should have updated timestamps

  Scenario: Delete a market
    Given I have a market with ticker "TEST-2024" in Firebase
    When I delete the market by ticker "TEST-2024"
    Then the market should be deleted successfully
    And the market should not be retrievable

  Scenario: Change detection with data hash
    Given I have a market with ticker "TEST-2024" in Firebase
    And the market has a data hash "abc123"
    When I update the market data
    And the new data has hash "def456"
    Then the data hash should be updated to "def456"
    And the updated_at timestamp should be updated

  Scenario: Market crawler runs successfully
    Given the market crawler is configured
    And the crawler interval is 30 minutes
    And Kalshi API is available
    When I start the market crawler
    Then the crawler should start successfully
    And the crawler should be scheduled to run every 30 minutes

  Scenario: Market crawler processes markets
    Given the market crawler is running
    And Kalshi API returns 100 open markets
    When the crawler runs
    Then it should retrieve 100 markets from Kalshi API
    And it should process all markets in batches
    And it should update or create markets in Firebase
    And the crawl should complete successfully

  Scenario: Market crawler handles API failures
    Given the market crawler is running
    And Kalshi API is unavailable
    When the crawler runs
    Then it should handle the API failure gracefully
    And it should retry with exponential backoff
    And it should log the failure

  Scenario: Market crawler handles database failures
    Given the market crawler is running
    And Kalshi API returns markets
    And Firebase is unavailable
    When the crawler runs
    Then it should handle the database failure gracefully
    And it should retry with exponential backoff
    And it should log the failure

  Scenario: Market crawler stops gracefully
    Given the market crawler is running
    When I stop the crawler
    Then the crawler should stop successfully
    And the scheduler should be shut down
    And all connections should be closed

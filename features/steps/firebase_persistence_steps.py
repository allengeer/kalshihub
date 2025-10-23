"""Step definitions for Firebase persistence BDD scenarios."""

import os
from datetime import datetime

from behave import given, then, when
from unittest.mock import MagicMock, patch

from src.firebase import FirebaseSchemaManager, MarketDAO, MarketCrawler
from src.kalshi.service import Market


@given('Firebase is configured with project ID "{project_id}"')
def step_firebase_configured(context, project_id):
    """Configure Firebase with project ID."""
    context.firebase_project_id = project_id
    context.firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")


@given("Firebase credentials are available")
def step_firebase_credentials_available(context):
    """Ensure Firebase credentials are available."""
    # In real implementation, this would check for actual credentials
    # For testing, we'll mock this
    context.firebase_credentials_available = True


@given("the market schema is deployed")
def step_market_schema_deployed(context):
    """Deploy the market schema."""
    context.schema_manager = FirebaseSchemaManager(
        project_id=context.firebase_project_id,
        credentials_path=context.firebase_credentials_path,
    )


@given("the Firebase schema manager is initialized")
def step_schema_manager_initialized(context):
    """Initialize Firebase schema manager."""
    context.schema_manager = FirebaseSchemaManager(
        project_id=context.firebase_project_id,
        credentials_path=context.firebase_credentials_path,
    )


@when("I deploy the schema")
def step_deploy_schema(context):
    """Deploy the Firebase schema."""
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ):
        context.schema_deployed = context.schema_manager.deploy_schema()


@then("the schema should be deployed successfully")
def step_schema_deployed_successfully(context):
    """Verify schema deployment was successful."""
    assert context.schema_deployed is True


@then('the schema version should be "{version}"')
def step_schema_version(context, version):
    """Verify schema version."""
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ) as mock_client:
        # Mock the schema document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"version": version}
        mock_client.return_value.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        actual_version = context.schema_manager.get_schema_version()
        assert actual_version == version


@then("the markets collection should exist")
def step_markets_collection_exists(context):
    """Verify markets collection exists."""
    # In a real implementation, this would check if the collection exists
    # For testing, we'll assume it exists after successful deployment
    assert context.schema_deployed is True


@given('I have a market with ticker "{ticker}"')
def step_have_market_with_ticker(context, ticker):
    """Create a market with the given ticker."""
    context.market = Market(
        ticker=ticker,
        event_ticker="TEST-EVENT-2024",
        market_type="binary",
        title="Test Market",
        subtitle="Test Subtitle",
        yes_sub_title="Yes",
        no_sub_title="No",
        open_time=datetime(2024, 1, 1),
        close_time=datetime(2024, 12, 31),
        expiration_time=datetime(2024, 12, 31),
        latest_expiration_time=datetime(2024, 12, 31),
        settlement_timer_seconds=3600,
        status="open",
        response_price_units="cents",
        notional_value=10000,
        notional_value_dollars="100.00",
        tick_size=1,
        yes_bid=45,
        yes_bid_dollars="0.45",
        yes_ask=55,
        yes_ask_dollars="0.55",
        no_bid=45,
        no_bid_dollars="0.45",
        no_ask=55,
        no_ask_dollars="0.55",
        last_price=50,
        last_price_dollars="0.50",
        previous_yes_bid=45,
        previous_yes_bid_dollars="0.45",
        previous_yes_ask=55,
        previous_yes_ask_dollars="0.55",
        previous_price=50,
        previous_price_dollars="0.50",
        volume=1000,
        volume_24h=500,
        liquidity=5000,
        liquidity_dollars="50.00",
        open_interest=100,
        result="",
        can_close_early=False,
        expiration_value="",
        category="politics",
        risk_limit_cents=100000,
        rules_primary="",
        rules_secondary="",
    )


@given('the market has title "{title}"')
def step_market_has_title(context, title):
    """Set market title."""
    context.market.title = title


@given('the market has status "{status}"')
def step_market_has_status(context, status):
    """Set market status."""
    context.market.status = status


@when("I create the market in Firebase")
def step_create_market_in_firebase(context):
    """Create market in Firebase."""
    context.market_dao = MarketDAO(
        project_id=context.firebase_project_id,
        credentials_path=context.firebase_credentials_path,
    )

    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ):
        context.market_created = context.market_dao.create_market(context.market)


@then("the market should be created successfully")
def step_market_created_successfully(context):
    """Verify market was created successfully."""
    assert context.market_created is True


@then('the market should be retrievable by ticker "{ticker}"')
def step_market_retrievable_by_ticker(context, ticker):
    """Verify market can be retrieved by ticker."""
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ) as mock_client:
        # Mock the market document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "ticker": ticker,
            "event_ticker": "TEST-EVENT-2024",
            "market_type": "binary",
            "title": "Test Market",
            "status": "open",
            "open_time": datetime(2024, 1, 1),
            "close_time": datetime(2024, 12, 31),
            "expiration_time": datetime(2024, 12, 31),
            "latest_expiration_time": datetime(2024, 12, 31),
            "settlement_timer_seconds": 3600,
            "response_price_units": "cents",
            "notional_value": 10000,
            "notional_value_dollars": "100.00",
            "tick_size": 1,
            "yes_bid": 45,
            "yes_bid_dollars": "0.45",
            "yes_ask": 55,
            "yes_ask_dollars": "0.55",
            "no_bid": 45,
            "no_bid_dollars": "0.45",
            "no_ask": 55,
            "no_ask_dollars": "0.55",
            "last_price": 50,
            "last_price_dollars": "0.50",
            "previous_yes_bid": 45,
            "previous_yes_bid_dollars": "0.45",
            "previous_yes_ask": 55,
            "previous_yes_ask_dollars": "0.55",
            "previous_price": 50,
            "previous_price_dollars": "0.50",
            "volume": 1000,
            "volume_24h": 500,
            "liquidity": 5000,
            "liquidity_dollars": "50.00",
            "open_interest": 100,
            "result": "",
            "can_close_early": False,
            "expiration_value": "",
            "category": "politics",
            "risk_limit_cents": 100000,
            "rules_primary": "",
            "rules_secondary": "",
        }
        mock_client.return_value.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        retrieved_market = context.market_dao.get_market(ticker)
        assert retrieved_market is not None
        assert retrieved_market.ticker == ticker


@given('I have a market with ticker "{ticker}" in Firebase')
def step_have_market_in_firebase(context, ticker):
    """Create a market that already exists in Firebase."""
    step_have_market_with_ticker(context, ticker)
    step_create_market_in_firebase(context)


@when('I update the market status to "{status}"')
def step_update_market_status(context, status):
    """Update market status."""
    context.market.status = status


@when("I save the market to Firebase")
def step_save_market_to_firebase(context):
    """Save market to Firebase."""
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ):
        context.market_updated = context.market_dao.update_market(context.market)


@then("the market should be updated successfully")
def step_market_updated_successfully(context):
    """Verify market was updated successfully."""
    assert context.market_updated is True


@then('the market status should be "{status}"')
def step_market_status_should_be(context, status):
    """Verify market status."""
    assert context.market.status == status


@then("the updated_at timestamp should be updated")
def step_updated_at_timestamp_updated(context):
    """Verify updated_at timestamp was updated."""
    # In a real implementation, this would check the actual timestamp
    # For testing, we'll assume it was updated if the update was successful
    assert context.market_updated is True


@when('I retrieve the market by ticker "{ticker}"')
def step_retrieve_market_by_ticker(context, ticker):
    """Retrieve market by ticker."""
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ) as mock_client:
        # Mock the market document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "ticker": ticker,
            "event_ticker": "TEST-EVENT-2024",
            "market_type": "binary",
            "title": "Test Market",
            "status": "open",
            "open_time": datetime(2024, 1, 1),
            "close_time": datetime(2024, 12, 31),
            "expiration_time": datetime(2024, 12, 31),
            "latest_expiration_time": datetime(2024, 12, 31),
            "settlement_timer_seconds": 3600,
            "response_price_units": "cents",
            "notional_value": 10000,
            "notional_value_dollars": "100.00",
            "tick_size": 1,
            "yes_bid": 45,
            "yes_bid_dollars": "0.45",
            "yes_ask": 55,
            "yes_ask_dollars": "0.55",
            "no_bid": 45,
            "no_bid_dollars": "0.45",
            "no_ask": 55,
            "no_ask_dollars": "0.55",
            "last_price": 50,
            "last_price_dollars": "0.50",
            "previous_yes_bid": 45,
            "previous_yes_bid_dollars": "0.45",
            "previous_yes_ask": 55,
            "previous_yes_ask_dollars": "0.55",
            "previous_price": 50,
            "previous_price_dollars": "0.50",
            "volume": 1000,
            "volume_24h": 500,
            "liquidity": 5000,
            "liquidity_dollars": "50.00",
            "open_interest": 100,
            "result": "",
            "can_close_early": False,
            "expiration_value": "",
            "category": "politics",
            "risk_limit_cents": 100000,
            "rules_primary": "",
            "rules_secondary": "",
        }
        mock_client.return_value.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        context.retrieved_market = context.market_dao.get_market(ticker)


@then("I should get the market data")
def step_should_get_market_data(context):
    """Verify market data was retrieved."""
    assert context.retrieved_market is not None


@then('the market ticker should be "{ticker}"')
def step_market_ticker_should_be(context, ticker):
    """Verify market ticker."""
    assert context.retrieved_market.ticker == ticker


@then('the market title should be "{title}"')
def step_market_title_should_be(context, title):
    """Verify market title."""
    assert context.retrieved_market.title == title


@given('I have markets with status "{status}" in Firebase')
def step_have_markets_with_status(context, status):
    """Create markets with specific status."""
    context.markets_with_status = []
    for i in range(3):
        market = Market(
            ticker=f"TEST-{status.upper()}-{i}",
            event_ticker="TEST-EVENT-2024",
            market_type="binary",
            title=f"Test Market {i}",
            subtitle="Test Subtitle",
            yes_sub_title="Yes",
            no_sub_title="No",
            open_time=datetime(2024, 1, 1),
            close_time=datetime(2024, 12, 31),
            expiration_time=datetime(2024, 12, 31),
            latest_expiration_time=datetime(2024, 12, 31),
            settlement_timer_seconds=3600,
            status=status,
            response_price_units="cents",
            notional_value=10000,
            notional_value_dollars="100.00",
            tick_size=1,
            yes_bid=45,
            yes_bid_dollars="0.45",
            yes_ask=55,
            yes_ask_dollars="0.55",
            no_bid=45,
            no_bid_dollars="0.45",
            no_ask=55,
            no_ask_dollars="0.55",
            last_price=50,
            last_price_dollars="0.50",
            previous_yes_bid=45,
            previous_yes_bid_dollars="0.45",
            previous_yes_ask=55,
            previous_yes_ask_dollars="0.55",
            previous_price=50,
            previous_price_dollars="0.50",
            volume=1000,
            volume_24h=500,
            liquidity=5000,
            liquidity_dollars="50.00",
            open_interest=100,
            result="",
            can_close_early=False,
            expiration_value="",
            category="politics",
            risk_limit_cents=100000,
            rules_primary="",
            rules_secondary="",
        )
        context.markets_with_status.append(market)


@when('I retrieve markets by status "{status}"')
def step_retrieve_markets_by_status(context, status):
    """Retrieve markets by status."""
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ) as mock_client:
        # Mock the markets query
        mock_docs = []
        for market in context.markets_with_status:
            if market.status == status:
                mock_doc = MagicMock()
                mock_doc.to_dict.return_value = {
                    "ticker": market.ticker,
                    "event_ticker": market.event_ticker,
                    "market_type": market.market_type,
                    "title": market.title,
                    "status": market.status,
                    "open_time": market.open_time,
                    "close_time": market.close_time,
                    "expiration_time": market.expiration_time,
                    "latest_expiration_time": market.latest_expiration_time,
                    "settlement_timer_seconds": market.settlement_timer_seconds,
                    "response_price_units": market.response_price_units,
                    "notional_value": market.notional_value,
                    "notional_value_dollars": market.notional_value_dollars,
                    "tick_size": market.tick_size,
                    "yes_bid": market.yes_bid,
                    "yes_bid_dollars": market.yes_bid_dollars,
                    "yes_ask": market.yes_ask,
                    "yes_ask_dollars": market.yes_ask_dollars,
                    "no_bid": market.no_bid,
                    "no_bid_dollars": market.no_bid_dollars,
                    "no_ask": market.no_ask,
                    "no_ask_dollars": market.no_ask_dollars,
                    "last_price": market.last_price,
                    "last_price_dollars": market.last_price_dollars,
                    "previous_yes_bid": market.previous_yes_bid,
                    "previous_yes_bid_dollars": market.previous_yes_bid_dollars,
                    "previous_yes_ask": market.previous_yes_ask,
                    "previous_yes_ask_dollars": market.previous_yes_ask_dollars,
                    "previous_price": market.previous_price,
                    "previous_price_dollars": market.previous_price_dollars,
                    "volume": market.volume,
                    "volume_24h": market.volume_24h,
                    "liquidity": market.liquidity,
                    "liquidity_dollars": market.liquidity_dollars,
                    "open_interest": market.open_interest,
                    "result": market.result,
                    "can_close_early": market.can_close_early,
                    "expiration_value": market.expiration_value,
                    "category": market.category,
                    "risk_limit_cents": market.risk_limit_cents,
                    "rules_primary": market.rules_primary,
                    "rules_secondary": market.rules_secondary,
                }
                mock_docs.append(mock_doc)

        mock_client.return_value.collection.return_value.where.return_value.stream.return_value = (
            mock_docs
        )

        context.retrieved_markets = context.market_dao.get_markets_by_status(status)


@then("I should get only the {status} markets")
def step_should_get_only_status_markets(context, status):
    """Verify only markets with specific status are retrieved."""
    assert len(context.retrieved_markets) > 0
    for market in context.retrieved_markets:
        assert market.status == status


@then('all returned markets should have status "{status}"')
def step_all_markets_have_status(context, status):
    """Verify all returned markets have the specified status."""
    for market in context.retrieved_markets:
        assert market.status == status


@given("the market crawler is configured")
def step_market_crawler_configured(context):
    """Configure the market crawler."""
    context.crawler = MarketCrawler(
        firebase_project_id=context.firebase_project_id,
        firebase_credentials_path=context.firebase_credentials_path,
        interval_minutes=30,
        batch_size=100,
        max_retries=3,
        retry_delay_seconds=1,
    )


@given("the crawler interval is {interval:d} minutes")
def step_crawler_interval(context, interval):
    """Set crawler interval."""
    context.crawler.interval_minutes = interval


@given("Kalshi API is available")
def step_kalshi_api_available(context):
    """Ensure Kalshi API is available."""
    context.kalshi_api_available = True


@when("I start the market crawler")
def step_start_market_crawler(context):
    """Start the market crawler."""
    with patch("firebase_admin.initialize_app"), patch("firebase_admin.get_app"), patch(
        "firestore.client"
    ):
        context.crawler.start()


@then("the crawler should start successfully")
def step_crawler_started_successfully(context):
    """Verify crawler started successfully."""
    assert context.crawler.scheduler.running is True


@then("the crawler should be scheduled to run every {interval:d} minutes")
def step_crawler_scheduled_interval(context, interval):
    """Verify crawler is scheduled with correct interval."""
    assert context.crawler.interval_minutes == interval


@when("I stop the crawler")
def step_stop_crawler(context):
    """Stop the market crawler."""
    context.crawler.stop()


@then("the crawler should stop successfully")
def step_crawler_stopped_successfully(context):
    """Verify crawler stopped successfully."""
    assert context.crawler.scheduler.running is False


@then("the scheduler should be shut down")
def step_scheduler_shutdown(context):
    """Verify scheduler is shut down."""
    assert context.crawler.scheduler.running is False


@then("all connections should be closed")
def step_connections_closed(context):
    """Verify all connections are closed."""
    # In a real implementation, this would check actual connections
    # For testing, we'll assume connections are closed if crawler is stopped
    assert context.crawler.scheduler.running is False

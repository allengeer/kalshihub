# Kalshi API Service Examples

This directory contains example scripts demonstrating how to use the Kalshi API service.

## Available Examples

### 1. `simple_test.py` - Basic Functionality Test
Tests the core functionality without hitting the API:
```bash
python examples/simple_test.py
```

**What it tests:**
- Service initialization
- Rate limiting functionality
- Market data parsing
- Async context manager

### 2. `mock_example.py` - Full Feature Demo with Mocked Data
Demonstrates all features using mocked data to avoid API calls:
```bash
python examples/mock_example.py
```

**What it demonstrates:**
- Basic market retrieval
- Pagination with `getAllOpenMarkets`
- Rate limiting behavior
- Filtering capabilities

### 3. `kalshi_example.py` - Real API Example
Uses the actual Kalshi API (may fail due to API response format):
```bash
python examples/kalshi_example.py
```

**What it demonstrates:**
- Real API integration
- Error handling
- Rate limiting with actual delays

## Running the Examples

1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run any example:**
   ```bash
   python examples/simple_test.py
   python examples/mock_example.py
   python examples/kalshi_example.py
   ```

## Notes

- The `simple_test.py` and `mock_example.py` scripts will always work as they don't depend on the external API
- The `kalshi_example.py` script may fail due to API response format differences
- All examples demonstrate the rate limiting and aggregator functionality

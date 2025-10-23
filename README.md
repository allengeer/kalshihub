# Kalshi Trading Solution

A Python-based trading solution for the Kalshi prediction market platform.

## Overview

This project provides tools and utilities for automated trading on Kalshi, including market analysis, position management, and risk controls.

## Features

- [ ] Market data integration
- [ ] Trading algorithms
- [ ] Risk management
- [ ] Portfolio tracking
- [ ] Performance analytics

## Requirements

- Python 3.13+
- Virtual environment (included in this repository)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd kalshihub
```

2. Activate the virtual environment:
```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up pre-commit hooks (recommended):
```bash
make pre-commit-install
```

## Usage

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the main application
python main.py
```

## Configuration

Create a `.env` file in the root directory with your configuration:

```env
KALSHI_API_KEY=your_api_key_here
KALSHI_API_SECRET=your_api_secret_here
```

## Development

### Project Structure

```
kalshihub/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
├── venv/                   # Virtual environment
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not tracked)
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── CHANGELOG.md           # Version history
└── AGENTS.md              # AI agent documentation
```

### Running Tests

```bash
# Run all CI checks locally
make ci-local

# Or run tests individually
python -m pytest tests/

# Run BDD tests with Behave
make bdd
```

### BDD Testing

This project uses [Behave](https://behave.readthedocs.io/) for Behavior-Driven Development (BDD) testing with Gherkin scenarios.

```bash
# Run BDD tests
make bdd

# Or run directly
behave features/ -v
```

BDD tests are located in the `features/` directory and use Gherkin syntax to describe application behavior.

### Coverage Tracking

This project uses [Codecov](https://codecov.io) for coverage tracking. Coverage reports are automatically uploaded on every CI run.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license information here]

## Disclaimer

This software is for educational and research purposes only. Trading involves risk and you should not invest money you cannot afford to lose. The authors are not responsible for any financial losses incurred through the use of this software.

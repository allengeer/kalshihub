# AI Agents Documentation

This document describes the AI agents and automated systems used in the Kalshi Trading Solution, along with our development workflow and quality standards.

## Overview

The Kalshi Trading Solution leverages AI agents to perform various trading and analysis tasks. This document outlines the agents' capabilities, configurations, usage patterns, and our development workflow requirements.

## Development Workflow

### Pull Request (PR) Structure

All pull requests must follow the **WHAT, WHY, HOW** structure:

#### **WHAT**
- Clear, concise description of what the PR does
- List of specific changes made
- Files modified/added/deleted

#### **WHY**
- Business justification for the changes
- Problem being solved
- Expected outcomes and benefits

#### **HOW**
- Technical approach and implementation details
- Architecture decisions made
- Any breaking changes or migration steps

### Commit Message Structure

All commit messages must follow this format:

```
<type>(<scope>): <description> [Closes #<issue_number>]

<body>

<footer>
```

#### Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples:
```
feat(trading): Add risk management agent [Closes #123]

Implements a new risk management agent that monitors portfolio
exposure and enforces position limits based on market volatility.

- Add RiskManagementAgent class
- Implement position limit enforcement
- Add risk monitoring dashboard
```

### GitHub Issue Workflow

1. **Create Issue First**: Before starting any new feature work, create a GitHub issue
2. **Issue Requirements**:
   - Clear title describing the feature/fix
   - Detailed description with acceptance criteria
   - Label appropriately (enhancement, bug, documentation, etc.)
   - Assign to appropriate milestone
3. **Branch Creation**: Create feature branch from `main` using the issue number
   ```
   git checkout main
   git pull origin main
   git checkout -b feature/123-add-risk-management-agent
   ```

### Quality Requirements

#### Unit Test Coverage
- **Minimum 80% code coverage** for all new features
- All critical business logic must have comprehensive test coverage
- Use pytest with coverage reporting:
  ```bash
  make test  # Runs tests with coverage
  ```

#### Gherkin Scenarios
- **All features must include Gherkin scenarios** using the specbyexample rule
- Define acceptance criteria in Given-When-Then format
- Examples:
  ```gherkin
  Feature: Risk Management
    As a trader
    I want to be notified when my position exceeds risk limits
    So that I can manage my portfolio risk effectively

  Scenario: Position limit exceeded
    Given I have a position worth $10,000
    And my risk limit is $5,000
    When the position value increases to $6,000
    Then I should receive a risk alert
    And my trading should be suspended
  ```

#### Component Testing
- **All features connecting to live services** require component tests
- Test against staging/sandbox environments
- Include integration tests for external API calls
- Mock external dependencies in unit tests

### Development Standards

#### Code Quality
- All code must pass linting (`make lint`)
- Code must be formatted with black (`make format`)
- Type hints required for all public functions
- Docstrings required for all classes and functions

#### Testing Strategy
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Component Tests**: Test against real services (staging)
- **End-to-End Tests**: Test complete user workflows

#### Documentation Requirements
- Update README.md for new features
- Add/update API documentation
- Include code examples and usage patterns
- Update CHANGELOG.md for user-facing changes

## Agent Architecture

### Core Agents

#### 1. Market Analysis Agent
- **Purpose**: Analyzes market conditions and trends
- **Capabilities**:
  - Price movement analysis
  - Volume pattern recognition
  - Market sentiment assessment
  - Risk indicator monitoring

#### 2. Trading Execution Agent
- **Purpose**: Executes trading strategies based on analysis
- **Capabilities**:
  - Order placement and management
  - Position sizing calculations
  - Risk management enforcement
  - Trade execution optimization

#### 3. Risk Management Agent
- **Purpose**: Monitors and enforces risk controls
- **Capabilities**:
  - Portfolio risk assessment
  - Position limit enforcement
  - Drawdown monitoring
  - Emergency stop mechanisms

#### 4. Portfolio Management Agent
- **Purpose**: Manages overall portfolio allocation and rebalancing
- **Capabilities**:
  - Asset allocation optimization
  - Rebalancing strategies
  - Performance tracking
  - Diversification monitoring

## Agent Configuration

### Environment Variables

```env
# Agent Configuration
AGENT_MODE=development  # development, production
LOG_LEVEL=INFO         # DEBUG, INFO, WARNING, ERROR
MAX_POSITION_SIZE=1000 # Maximum position size per trade
RISK_TOLERANCE=0.02    # Maximum risk per trade (2%)
```

### Agent Settings

Each agent can be configured through JSON configuration files:

```json
{
  "market_analysis": {
    "update_interval": 60,
    "indicators": ["rsi", "macd", "bollinger_bands"],
    "sentiment_sources": ["news", "social_media", "options_flow"]
  },
  "trading_execution": {
    "max_orders_per_minute": 10,
    "slippage_tolerance": 0.001,
    "order_timeout": 30
  }
}
```

## Agent Communication

Agents communicate through a message bus system:

- **Events**: Market data updates, trade executions, risk alerts
- **Commands**: Execute trades, update positions, modify strategies
- **Queries**: Request market data, portfolio status, performance metrics

## Usage Examples

### Starting Agents

```python
from src.agents import AgentManager

# Initialize agent manager
manager = AgentManager()

# Start all agents
manager.start_all()

# Start specific agent
manager.start_agent("market_analysis")
```

### Custom Agent Development

```python
from src.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
    
    def process_message(self, message):
        # Implement custom logic
        pass
    
    def run(self):
        # Main agent loop
        while self.running:
            # Agent logic here
            pass
```

## Monitoring and Logging

### Agent Status

Monitor agent health and performance:

```python
# Check agent status
status = manager.get_agent_status("market_analysis")
print(f"Agent running: {status['running']}")
print(f"Last update: {status['last_update']}")
```

### Logging

All agents log their activities:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agent logs will be written to logs/agents/
```

## Best Practices

1. **Error Handling**: Implement robust error handling in all agents
2. **Resource Management**: Monitor memory and CPU usage
3. **Failover**: Implement backup strategies for critical agents
4. **Testing**: Write comprehensive tests for agent logic
5. **Documentation**: Document all agent configurations and behaviors

## Troubleshooting

### Common Issues

1. **Agent Not Starting**: Check configuration and dependencies
2. **High CPU Usage**: Optimize agent loops and reduce update frequency
3. **Memory Leaks**: Monitor object creation and cleanup
4. **Communication Errors**: Verify message bus connectivity

### Debug Mode

Enable debug mode for detailed logging:

```env
LOG_LEVEL=DEBUG
AGENT_MODE=development
```

## Future Enhancements

- [ ] Machine learning model integration
- [ ] Advanced sentiment analysis
- [ ] Multi-market support
- [ ] Real-time strategy optimization
- [ ] Agent performance analytics

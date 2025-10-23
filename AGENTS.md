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



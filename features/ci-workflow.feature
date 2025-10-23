Feature: GitHub Actions CI Workflow
  As a developer
  I want automated CI checks on pull requests
  So that code quality and test coverage standards are enforced

  Background:
    Given the project has a GitHub Actions workflow configured
    And the workflow runs on pull requests to main and develop branches

  Scenario: CI workflow runs on pull request
    Given a developer creates a pull request
    When the pull request is opened or updated
    Then the CI workflow should automatically trigger
    And all CI checks should run

  Scenario: Test suite execution
    Given the CI workflow is running
    When the test step executes
    Then pytest should run all tests in the tests/ directory
    And test results should be reported
    And all tests should pass

  Scenario: Code coverage enforcement
    Given the CI workflow is running
    When the coverage step executes
    Then code coverage should be calculated for the src/ directory
    And coverage should meet the minimum 80% requirement
    And coverage report should be generated
    And coverage should be uploaded to Codecov

  Scenario: Code quality checks
    Given the CI workflow is running
    When the linting step executes
    Then flake8 should check code style and complexity
    And mypy should perform type checking
    And black should verify code formatting
    And all quality checks should pass

  Scenario: CI workflow failure on quality issues
    Given a pull request has code quality issues
    When the CI workflow runs
    Then the workflow should fail if:
      | Issue Type | Failure Condition |
      | Tests fail | Any test in the suite fails |
      | Low coverage | Code coverage is below 80% |
      | Linting errors | flake8 finds style violations |
      | Type errors | mypy finds type checking issues |
      | Formatting issues | black detects formatting problems |

  Scenario: CI workflow success on quality code
    Given a pull request has high-quality code
    When the CI workflow runs
    Then all tests should pass
    And code coverage should be 80% or higher
    And all linting checks should pass
    And all type checks should pass
    And all formatting checks should pass
    And the workflow should succeed

  Scenario: Coverage report generation
    Given the CI workflow is running
    When the coverage step executes
    Then an HTML coverage report should be generated
    And the coverage report should be uploaded as an artifact
    And developers should be able to download the report

  Scenario: Dependency caching
    Given the CI workflow is running
    When the workflow installs dependencies
    Then pip dependencies should be cached
    And subsequent runs should use cached dependencies
    And installation time should be reduced

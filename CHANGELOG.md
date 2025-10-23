# Changelog

All notable changes to the Kalshi Trading Solution will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Python 3.13 virtual environment
- Basic project structure
- README.md with installation and usage instructions
- CHANGELOG.md for version tracking
- AGENTS.md with comprehensive development workflow and quality standards
- Development workflow requirements:
  - PR structure (WHAT, WHY, HOW format)
  - Commit message guidelines with GitHub issue linking
  - GitHub issue workflow for feature development
  - 80% unit test coverage requirement
  - Gherkin scenarios requirement for all features
  - Component testing for live service integrations
- Enhanced Makefile with coverage reporting commands
- Code quality standards and testing strategy
- GitHub Actions CI workflow for automated PR validation:
  - Automated test execution with pytest
  - Code coverage enforcement (80% minimum)
  - Linting with flake8 and mypy
  - Code formatting checks with black
  - Coverage reporting and artifact upload
  - Dependency caching for faster builds
- Comprehensive test suite for CI workflow functionality
- Gherkin scenarios for CI workflow feature validation

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [0.1.0] - 2024-01-XX

### Added
- Project initialization
- Virtual environment setup
- Basic documentation structure

---

## Version Format

- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

## How to Update This File

When making changes, add them to the [Unreleased] section under the appropriate category. When releasing a new version, move the changes from [Unreleased] to a new version section with the current date.

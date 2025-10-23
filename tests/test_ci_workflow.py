"""Tests for CI workflow functionality."""

import os
from pathlib import Path

import pytest

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class TestCIWorkflow:
    """Test cases for GitHub Actions CI workflow."""

    def test_ci_workflow_file_exists(self):
        """Test that CI workflow file exists."""
        workflow_path = Path(".github/workflows/ci.yml")
        assert workflow_path.exists(), "CI workflow file should exist"

    def test_ci_workflow_is_valid_yaml(self):
        """Test that CI workflow file contains valid YAML."""
        if not YAML_AVAILABLE:
            pytest.skip("PyYAML not available")
            
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_config = yaml.safe_load(file)
        
        assert workflow_config is not None, "Workflow file should contain valid YAML"
        assert isinstance(workflow_config, dict), "Workflow should be a dictionary"

    def test_ci_workflow_has_required_structure(self):
        """Test that CI workflow has required structure."""
        if not YAML_AVAILABLE:
            pytest.skip("PyYAML not available")
            
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_config = yaml.safe_load(file)
        
        # Check required top-level keys
        required_keys = ['name', 'on', 'jobs']
        for key in required_keys:
            assert key in workflow_config, f"Workflow should have '{key}' key"

    def test_ci_workflow_triggers(self):
        """Test that CI workflow has correct triggers."""
        if not YAML_AVAILABLE:
            pytest.skip("PyYAML not available")
            
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_config = yaml.safe_load(file)
        
        triggers = workflow_config.get('on', {})
        
        # Check push triggers
        assert 'push' in triggers, "Workflow should trigger on push"
        assert 'branches' in triggers['push'], "Push trigger should specify branches"
        assert 'main' in triggers['push']['branches'], "Should trigger on main branch"
        assert 'develop' in triggers['push']['branches'], "Should trigger on develop branch"
        
        # Check pull_request triggers
        assert 'pull_request' in triggers, "Workflow should trigger on pull requests"
        assert 'branches' in triggers['pull_request'], "PR trigger should specify branches"
        assert 'main' in triggers['pull_request']['branches'], "Should trigger on PRs to main"
        assert 'develop' in triggers['pull_request']['branches'], "Should trigger on PRs to develop"

    def test_ci_workflow_job_structure(self):
        """Test that CI workflow job has correct structure."""
        if not YAML_AVAILABLE:
            pytest.skip("PyYAML not available")
            
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_config = yaml.safe_load(file)
        
        jobs = workflow_config.get('jobs', {})
        assert 'test' in jobs, "Should have a 'test' job"
        
        test_job = jobs['test']
        assert 'runs-on' in test_job, "Test job should specify runs-on"
        assert test_job['runs-on'] == 'ubuntu-latest', "Should run on ubuntu-latest"

    def test_ci_workflow_python_version(self):
        """Test that CI workflow uses Python 3.13."""
        if not YAML_AVAILABLE:
            pytest.skip("PyYAML not available")
            
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_config = yaml.safe_load(file)
        
        test_job = workflow_config['jobs']['test']
        strategy = test_job.get('strategy', {})
        matrix = strategy.get('matrix', {})
        python_versions = matrix.get('python-version', [])
        
        assert 3.13 in python_versions, "Should use Python 3.13"

    def test_ci_workflow_has_required_steps(self):
        """Test that CI workflow has all required steps."""
        if not YAML_AVAILABLE:
            pytest.skip("PyYAML not available")
            
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_config = yaml.safe_load(file)
        
        test_job = workflow_config['jobs']['test']
        steps = test_job.get('steps', [])
        
        # Extract step names
        step_names = []
        for step in steps:
            if 'name' in step:
                step_names.append(step['name'])
        
        # Check for required steps
        required_steps = [
            'Set up Python',
            'Install dependencies',
            'Lint with flake8',
            'Type check with mypy',
            'Check code formatting with black',
            'Test with pytest and coverage'
        ]
        
        for required_step in required_steps:
            assert any(required_step in step_name for step_name in step_names), \
                f"Should have step containing '{required_step}'"

    def test_ci_workflow_coverage_requirement(self):
        """Test that CI workflow enforces 80% coverage requirement."""
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_content = file.read()
        
        assert '--cov-fail-under=80' in workflow_content, \
            "Should enforce 80% minimum coverage requirement"

    def test_gherkin_scenarios_exist(self):
        """Test that Gherkin scenarios file exists."""
        scenarios_path = Path("features/ci-workflow.feature")
        assert scenarios_path.exists(), "Gherkin scenarios file should exist"

    def test_gherkin_scenarios_content(self):
        """Test that Gherkin scenarios file has proper content."""
        scenarios_path = Path("features/ci-workflow.feature")
        
        with open(scenarios_path, 'r') as file:
            content = file.read()
        
        # Check for key Gherkin keywords
        assert 'Feature:' in content, "Should contain Feature keyword"
        assert 'Scenario:' in content, "Should contain Scenario keywords"
        assert 'Given' in content, "Should contain Given steps"
        assert 'When' in content, "Should contain When steps"
        assert 'Then' in content, "Should contain Then steps"

    def test_ci_workflow_artifact_upload(self):
        """Test that CI workflow uploads coverage artifacts."""
        workflow_path = Path(".github/workflows/ci.yml")
        
        with open(workflow_path, 'r') as file:
            workflow_content = file.read()
        
        assert 'upload-artifact' in workflow_content, \
            "Should upload coverage artifacts"
        assert 'coverage-report' in workflow_content, \
            "Should upload coverage report artifact"

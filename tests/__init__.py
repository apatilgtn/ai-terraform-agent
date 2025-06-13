
# tests/__init__.py
"""
Test suite for AI Terraform Agent
"""

# tests/conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import os

# Set test environment variables
os.environ.update({
    'GITHUB_TOKEN': 'test-token',
    'GITHUB_OWNER': 'test-owner',
    'GCP_PROJECT_ID': 'test-project',
    'GITHUB_REPO': 'test-repo'
})

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing."""
    client = AsyncMock()
    
    # Mock successful responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"object": {"sha": "abc123"}}
    
    client.get.return_value = mock_response
    client.post.return_value = mock_response
    client.put.return_value = mock_response
    
    return client

@pytest.fixture
def sample_terraform_config():
    """Sample Terraform configuration for testing."""
    return {
        "resource_type": "gcp_vm",
        "resource_name": "test_vm",
        "instance_name": "test-vm",
        "machine_type": "e2-micro",
        "image": "debian-cloud/debian-11",
        "disk_size": 20,
        "zone": "us-central1-a",
        "project_id": "test-project",
        "region": "us-central1",
        "environment": "test",
        "timestamp": "20240101120000",
        "metadata": 'startup-script = "echo Hello"',
        "tags": '["test"]',
        "instruction": "Create a test VM"
    }

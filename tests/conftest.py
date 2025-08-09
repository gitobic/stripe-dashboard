"""Pytest configuration and shared fixtures"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

# Test fixtures
from tests.fixtures.stripe_fixtures import (
    create_mock_charges,
    create_mock_customers,
    create_mock_subscriptions,
    MockStripeCharge,
    MockStripeCustomer,
    MockStripeSubscription
)

@pytest.fixture
def mock_charges():
    """Fixture providing mock Stripe charges"""
    return create_mock_charges(5)

@pytest.fixture
def mock_customers():
    """Fixture providing mock Stripe customers"""
    return create_mock_customers(3)

@pytest.fixture
def mock_subscriptions():
    """Fixture providing mock Stripe subscriptions"""
    return create_mock_subscriptions(5)

@pytest.fixture
def temp_data_dir():
    """Fixture providing temporary data directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up temporary data directory
        original_data_dir = os.environ.get('DATA_DIR', 'data')
        os.environ['DATA_DIR'] = temp_dir
        yield Path(temp_dir)
        # Restore original data directory
        os.environ['DATA_DIR'] = original_data_dir

@pytest.fixture
def mock_streamlit():
    """Fixture providing mocked streamlit components"""
    with patch('streamlit.session_state', {}) as mock_state, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.success') as mock_success:
        
        yield {
            'session_state': mock_state,
            'error': mock_error,
            'warning': mock_warning,
            'info': mock_info,
            'success': mock_success
        }

@pytest.fixture
def mock_stripe_api():
    """Fixture providing mocked Stripe API"""
    with patch('stripe.Charge') as mock_charge, \
         patch('stripe.Customer') as mock_customer, \
         patch('stripe.Subscription') as mock_subscription:
        
        yield {
            'Charge': mock_charge,
            'Customer': mock_customer,
            'Subscription': mock_subscription
        }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Auto-use fixture to set up test environment"""
    # Set test environment variables
    test_env = {
        'STRIPE_SECRET_KEY': 'sk_test_fake_key_for_testing',
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_fake_key_for_testing',
        'ANTHROPIC_API_KEY': 'fake_anthropic_key_for_testing',
        'GOOGLE_SERVICE_ACCOUNT_JSON': '{"type": "service_account", "project_id": "test"}'
    }
    
    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

@pytest.fixture
def mock_file_system():
    """Fixture providing mocked file system operations"""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('builtins.open') as mock_open:
        
        yield {
            'exists': mock_exists,
            'mkdir': mock_mkdir,
            'open': mock_open
        }

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location"""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        # Mark unit tests
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests (integration tests are typically slower)
        if "integration" in str(item.fspath) or "test_large" in item.name:
            item.add_marker(pytest.mark.slow)
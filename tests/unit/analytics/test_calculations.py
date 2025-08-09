"""Tests for analytics calculations module"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from analytics.calculations import (
    calculate_churn_metrics,
    calculate_customer_lifetime_value,
    forecast_revenue
)
from tests.fixtures.stripe_fixtures import (
    create_mock_subscriptions,
    create_mock_charges,
    MockStripeSubscription
)

class TestCalculateChurnMetrics:
    """Tests for calculate_churn_metrics function"""
    
    def test_empty_subscriptions(self):
        """Test churn calculation with no subscriptions"""
        result = calculate_churn_metrics([])
        
        assert result['total_subscriptions'] == 0
        assert result['active_subscriptions'] == 0
        assert result['churn_rate'] == 0
        assert result['trial_conversion_rate'] == 0
    
    def test_mixed_subscription_statuses(self):
        """Test churn calculation with various subscription statuses"""
        subscriptions = [
            MockStripeSubscription(status='active'),
            MockStripeSubscription(status='active'),
            MockStripeSubscription(status='trialing'),
            MockStripeSubscription(status='canceled'),
            MockStripeSubscription(status='canceled')
        ]
        
        result = calculate_churn_metrics(subscriptions)
        
        assert result['total_subscriptions'] == 5
        assert result['active_subscriptions'] == 2
        assert result['trialing_subscriptions'] == 1
        assert result['canceled_subscriptions'] == 2
        assert result['churn_rate'] == 40.0  # 2/5 * 100
        assert result['trial_conversion_rate'] == 66.67  # 2/(2+1) * 100, rounded
    
    def test_all_active_subscriptions(self):
        """Test churn calculation with all active subscriptions"""
        subscriptions = [
            MockStripeSubscription(status='active'),
            MockStripeSubscription(status='active'),
            MockStripeSubscription(status='active')
        ]
        
        result = calculate_churn_metrics(subscriptions)
        
        assert result['churn_rate'] == 0.0
        assert result['trial_conversion_rate'] == 100.0

class TestCalculateCustomerLifetimeValue:
    """Tests for calculate_customer_lifetime_value function"""
    
    def test_no_transactions(self):
        """Test CLV calculation with no transactions"""
        result = calculate_customer_lifetime_value('cus_test123', [])
        assert result == 0.0
    
    def test_single_transaction(self):
        """Test CLV calculation with single transaction"""
        charges = [create_mock_charges(1)[0]]
        charges[0].customer = Mock()
        charges[0].customer.id = 'cus_test123'
        charges[0].status = 'succeeded'
        charges[0].amount = 5000  # $50
        
        result = calculate_customer_lifetime_value('cus_test123', charges)
        assert result == 50.0  # Single transaction returns the amount
    
    def test_multiple_transactions_same_customer(self):
        """Test CLV calculation with multiple transactions for same customer"""
        charges = []
        base_time = datetime.now()
        
        for i in range(3):
            charge = Mock()
            charge.customer = Mock()
            charge.customer.id = 'cus_test123'
            charge.status = 'succeeded'
            charge.amount = 2000  # $20 each
            charge.created = int((base_time - timedelta(days=i*30)).timestamp())
            charges.append(charge)
        
        result = calculate_customer_lifetime_value('cus_test123', charges)
        # Should be > 60 (total spent) due to projection over 24 months
        assert result > 60.0
    
    def test_different_customer_filtering(self):
        """Test CLV calculation filters correct customer"""
        charges = []
        
        # Add charges for different customers
        for customer_id in ['cus_test123', 'cus_test456']:
            charge = Mock()
            charge.customer = Mock()
            charge.customer.id = customer_id
            charge.status = 'succeeded'
            charge.amount = 1000
            charge.created = int(datetime.now().timestamp())
            charges.append(charge)
        
        result = calculate_customer_lifetime_value('cus_test123', charges)
        # Should only consider transactions from cus_test123
        assert result == 10.0  # Single transaction for this customer

class TestForecastRevenue:
    """Tests for forecast_revenue function"""
    
    def test_empty_transactions(self):
        """Test revenue forecasting with no transactions"""
        result = forecast_revenue([])
        assert result == []
    
    def test_insufficient_data(self):
        """Test revenue forecasting with insufficient historical data"""
        charges = create_mock_charges(1)
        result = forecast_revenue(charges, months_ahead=3)
        assert result == []  # Not enough data for meaningful forecast
    
    def test_basic_forecasting(self):
        """Test basic revenue forecasting with trend"""
        charges = []
        base_time = datetime.now()
        
        # Create charges for last 4 months with increasing trend
        for i in range(4):
            charge = Mock()
            charge.status = 'succeeded'
            charge.amount = (i + 1) * 1000  # $10, $20, $30, $40
            # Set dates to different months
            month_date = base_time - timedelta(days=(3-i) * 30)
            charge.created = int(month_date.timestamp())
            charges.append(charge)
        
        result = forecast_revenue(charges, months_ahead=2)
        
        assert len(result) == 2
        assert all('month' in forecast for forecast in result)
        assert all('forecasted_revenue' in forecast for forecast in result)
        assert all('confidence' in forecast for forecast in result)
        
        # Confidence should decrease over time
        assert result[0]['confidence'] > result[1]['confidence']

class TestAnalyticsIntegration:
    """Integration tests for analytics calculations"""
    
    def test_full_analytics_pipeline(self):
        """Test complete analytics pipeline"""
        # Create realistic test data
        subscriptions = create_mock_subscriptions(10)
        charges = create_mock_charges(20)
        
        # Test churn metrics
        churn_metrics = calculate_churn_metrics(subscriptions)
        assert isinstance(churn_metrics, dict)
        assert all(key in churn_metrics for key in [
            'total_subscriptions', 'active_subscriptions', 
            'churn_rate', 'trial_conversion_rate'
        ])
        
        # Test CLV calculation
        clv = calculate_customer_lifetime_value('cus_test1', charges)
        assert isinstance(clv, (int, float))
        assert clv >= 0
        
        # Test forecasting
        forecast = forecast_revenue(charges, months_ahead=3)
        assert isinstance(forecast, list)
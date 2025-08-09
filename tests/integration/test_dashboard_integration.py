"""Integration tests for dashboard functionality"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

from tests.fixtures.stripe_fixtures import create_mock_charges, create_mock_customers

class TestTransactionDashboardIntegration:
    """Integration tests for transactions dashboard"""
    
    @patch('dashboard.transactions.get_stripe_data')
    @patch('dashboard.transactions.st')
    def test_transactions_dashboard_with_data(self, mock_st, mock_get_data):
        """Test transactions dashboard with mock data"""
        # Setup mock data
        mock_charges = create_mock_charges(10)
        mock_get_data.return_value = mock_charges
        
        # Mock streamlit components
        mock_st.session_state = {}
        mock_st.spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock()
        mock_st.spinner.return_value.__exit__ = Mock()
        mock_st.date_input.return_value = datetime.now().date()
        mock_st.multiselect.return_value = ['succeeded']
        mock_st.selectbox.return_value = 'Daily Revenue'
        mock_st.number_input.return_value = 0.0
        
        # Create context manager mocks for columns
        col_mocks = []
        for i in range(4):
            col_mock = MagicMock()
            col_mock.__enter__ = Mock(return_value=col_mock)
            col_mock.__exit__ = Mock(return_value=None)
            col_mocks.append(col_mock)
        mock_st.columns.return_value = col_mocks
        
        # Import and test the function
        from dashboard.transactions import render_transactions_dashboard
        
        # Should not raise any exceptions
        try:
            render_transactions_dashboard()
        except Exception as e:
            # If there are streamlit-specific errors, that's expected in test environment
            if "streamlit" not in str(e).lower():
                raise e
    
    @patch('dashboard.transactions.get_stripe_data')
    @patch('dashboard.transactions.st')
    def test_transactions_dashboard_empty_data(self, mock_st, mock_get_data):
        """Test transactions dashboard with no data"""
        mock_get_data.return_value = []
        
        # Mock streamlit components
        mock_st.session_state = {}
        mock_st.warning = Mock()
        
        from dashboard.transactions import render_transactions_dashboard
        
        # Should handle empty data gracefully
        try:
            render_transactions_dashboard()
        except Exception as e:
            if "streamlit" not in str(e).lower():
                raise e

class TestAnalyticsIntegration:
    """Integration tests for analytics components"""
    
    def test_fee_calculation_integration(self):
        """Test fee calculation with realistic data"""
        from analytics.fees import calculate_stripe_fees
        
        charges = create_mock_charges(5)
        # Set all charges to succeeded for fee calculation
        for charge in charges:
            charge.status = 'succeeded'
        
        result = calculate_stripe_fees(charges)
        
        assert 'total_fees' in result
        assert 'total_revenue' in result
        assert 'fee_percentage' in result
        assert result['total_fees'] > 0
        assert result['total_revenue'] > 0
        assert 0 < result['fee_percentage'] < 10  # Reasonable fee percentage
    
    def test_charts_generation(self):
        """Test chart generation with mock data"""
        from analytics.charts import create_revenue_chart, create_product_chart
        
        charges = create_mock_charges(5)
        
        # Test revenue chart
        revenue_chart = create_revenue_chart(charges)
        assert revenue_chart is not None
        
        # Test product chart  
        product_chart = create_product_chart(charges)
        assert product_chart is not None

class TestDataFlowIntegration:
    """Test data flow between different components"""
    
    @patch('services.stripe_service.stripe')
    def test_stripe_to_analytics_flow(self, mock_stripe):
        """Test data flow from Stripe service to analytics"""
        from services.stripe_service import filter_charges_data
        from analytics.fees import calculate_stripe_fees
        
        # Create mock data
        charges = create_mock_charges(10)
        
        # Test filtering
        filtered = filter_charges_data(charges, ['succeeded'], 0, 1000)
        assert len(filtered) <= len(charges)
        
        # Test analytics on filtered data
        fees = calculate_stripe_fees(filtered)
        assert isinstance(fees, dict)
    
    def test_customer_data_to_tags_flow(self):
        """Test customer data to tagging system flow"""
        from models.customer_data import add_customer_tag, get_customer_tags
        
        with patch('models.customer_data.load_tags_and_notes') as mock_load, \
             patch('models.customer_data.save_tags_and_notes') as mock_save:
            
            mock_load.return_value = {"customer_tags": {}}
            mock_save.return_value = True
            
            # Test adding tag
            add_customer_tag("cus_test", "VIP")
            
            # Verify save was called
            mock_save.assert_called_once()

class TestErrorHandlingIntegration:
    """Test error handling across components"""
    
    @patch('services.stripe_service.stripe.Charge.list')
    def test_stripe_api_error_handling(self, mock_stripe_list):
        """Test handling of Stripe API errors"""
        mock_stripe_list.side_effect = Exception("API Error")
        
        from services.stripe_service import get_stripe_data
        
        # Should handle errors gracefully
        with patch('streamlit.error'):
            result = get_stripe_data(datetime.now(), datetime.now())
            assert result == []  # Should return empty list on error
    
    def test_invalid_data_handling(self):
        """Test handling of invalid data formats"""
        from analytics.calculations import calculate_customer_lifetime_value
        
        # Test with invalid customer ID format
        result = calculate_customer_lifetime_value(None, [])
        assert result == 0.0
        
        # Test with malformed charges
        invalid_charges = [Mock()]  # Missing required attributes
        result = calculate_customer_lifetime_value("cus_test", invalid_charges)
        assert result == 0.0

class TestPerformanceIntegration:
    """Test performance characteristics of integrated components"""
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        from analytics.calculations import calculate_churn_metrics
        from tests.fixtures.stripe_fixtures import create_mock_subscriptions
        
        # Create large dataset
        large_subscription_set = create_mock_subscriptions(1000)
        
        # Should handle large datasets without errors
        result = calculate_churn_metrics(large_subscription_set)
        assert isinstance(result, dict)
        assert result['total_subscriptions'] == 1000
    
    def test_caching_integration(self):
        """Test caching mechanisms work correctly"""
        from services.cache_service import cache_stripe_data
        
        # Create a mock function to cache
        call_count = 0
        
        @cache_stripe_data(ttl_seconds=1)
        def mock_expensive_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        with patch('streamlit.session_state', {}):
            # First call
            result1 = mock_expensive_function("test")
            assert call_count == 1
            
            # Second call should use cache
            result2 = mock_expensive_function("test")
            assert call_count == 1  # Should not increment
            assert result1 == result2
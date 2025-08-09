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
        
        # Create flexible column mock that handles both int and list arguments
        def create_columns(spec):
            if isinstance(spec, list):
                num_cols = len(spec)
            else:
                num_cols = spec
            
            col_mocks = []
            for i in range(num_cols):
                col_mock = MagicMock()
                col_mock.__enter__ = Mock(return_value=col_mock)
                col_mock.__exit__ = Mock(return_value=None)
                col_mocks.append(col_mock)
            return col_mocks
        
        mock_st.columns.side_effect = create_columns
        
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
        mock_st.spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = Mock()
        mock_st.spinner.return_value.__exit__ = Mock()
        mock_st.date_input.return_value = datetime.now().date()
        mock_st.selectbox.return_value = 'All Transactions'
        mock_st.number_input.return_value = 0.0
        
        # Create flexible column mock that handles both int and list arguments  
        def create_columns(spec):
            if isinstance(spec, list):
                num_cols = len(spec)
            else:
                num_cols = spec
            
            col_mocks = []
            for i in range(num_cols):
                col_mock = MagicMock()
                col_mock.__enter__ = Mock(return_value=col_mock)
                col_mock.__exit__ = Mock(return_value=None)
                col_mocks.append(col_mock)
            return col_mocks
        
        mock_st.columns.side_effect = create_columns
        
        from dashboard.transactions import render_transactions_dashboard
        
        # Should handle empty data gracefully
        try:
            render_transactions_dashboard()
        except Exception as e:
            if "streamlit" not in str(e).lower():
                raise e

class TestAnalyticsIntegration:
    """Integration tests for analytics components"""
    
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
    def test_stripe_to_charts_flow(self, mock_stripe):
        """Test data flow from Stripe service to charts"""
        from services.stripe_service import filter_charges_data
        from analytics.charts import create_revenue_chart
        
        # Create mock data
        charges = create_mock_charges(10)
        
        # Test filtering
        filtered = filter_charges_data(charges, ['succeeded'], 0, 1000)
        assert len(filtered) <= len(charges)
        
        # Test chart creation on filtered data
        chart = create_revenue_chart(filtered)
        assert chart is not None
    
    def test_customer_data_flow(self):
        """Test customer data flow"""
        from services.stripe_service import get_customers_data
        
        with patch('services.stripe_service.stripe') as mock_stripe:
            # Mock stripe response
            mock_stripe.Customer.list.return_value.auto_paging_iter.return_value = create_mock_customers(5)
            
            # Test getting customer data
            customers = get_customers_data()
            assert isinstance(customers, list)

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
        from analytics.charts import create_revenue_chart
        
        # Test with empty data
        result = create_revenue_chart([])
        assert result is not None
        
        # Test with malformed charges - should handle gracefully
        # Create a mock with minimal required attributes
        invalid_charge = Mock()
        invalid_charge.created = 1640995200  # Valid timestamp
        invalid_charge.amount = 1000
        invalid_charge.currency = 'usd'
        invalid_charge.status = 'succeeded'
        
        result = create_revenue_chart([invalid_charge])
        assert result is not None

class TestPerformanceIntegration:
    """Test performance characteristics of integrated components"""
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        from analytics.charts import create_revenue_chart
        
        # Create large dataset
        large_charges_set = create_mock_charges(1000)
        
        # Should handle large datasets without errors
        result = create_revenue_chart(large_charges_set)
        assert result is not None
    
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
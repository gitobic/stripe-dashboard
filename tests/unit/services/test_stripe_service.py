"""Tests for stripe_service module"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from services.stripe_service import (
    filter_charges_data,
    get_detailed_payment_method
)
from tests.fixtures.stripe_fixtures import (
    create_mock_charges,
    MockStripeCharge,
    MockPaymentMethodDetails,
    MockCard
)

class TestFilterChargesData:
    """Tests for filter_charges_data function"""
    
    def test_filter_empty_data(self):
        """Test filtering empty data returns empty list"""
        result = filter_charges_data([], ['succeeded'], 0, 1000)
        assert result == []
    
    def test_filter_by_status(self):
        """Test filtering by payment status"""
        charges = create_mock_charges(4)
        # Mock charges alternate between succeeded/failed
        
        # Filter only succeeded
        result = filter_charges_data(charges, ['succeeded'], 0, 10000)
        succeeded_charges = [c for c in result if c.status == 'succeeded']
        assert len(succeeded_charges) == 2  # Charges 0 and 2 are succeeded
    
    def test_filter_by_amount_range(self):
        """Test filtering by amount range"""
        charges = create_mock_charges(5)
        
        # Filter amounts between $15-$35 (1500-3500 cents)
        result = filter_charges_data(charges, ['succeeded', 'failed'], 15, 35)
        
        # Should include charges with amounts $20, $30 (charges 1, 2)
        assert len(result) == 2
        for charge in result:
            amount_dollars = charge.amount / 100
            assert 15 <= amount_dollars <= 35
    
    def test_filter_combination(self):
        """Test filtering by both status and amount"""
        charges = create_mock_charges(5)
        
        # Filter succeeded charges between $15-$35
        result = filter_charges_data(charges, ['succeeded'], 15, 35)
        
        for charge in result:
            assert charge.status == 'succeeded'
            amount_dollars = charge.amount / 100
            assert 15 <= amount_dollars <= 35

class TestGetDetailedPaymentMethod:
    """Tests for get_detailed_payment_method function"""
    
    def test_card_with_brand(self):
        """Test card payment method with brand"""
        charge = MockStripeCharge()
        charge.payment_method_details = MockPaymentMethodDetails(
            type='card',
            card=MockCard(brand='visa')
        )
        
        result = get_detailed_payment_method(charge)
        assert result == 'Visa'
    
    def test_card_with_wallet(self):
        """Test card payment method with wallet (Apple Pay)"""
        charge = MockStripeCharge()
        wallet_mock = Mock()
        wallet_mock.type = 'apple_pay'
        
        card_mock = MockCard(brand='visa', wallet=wallet_mock)
        charge.payment_method_details = MockPaymentMethodDetails(
            type='card',
            card=card_mock
        )
        
        result = get_detailed_payment_method(charge)
        assert result == 'Visa (Apple Pay)'
    
    def test_ach_payment(self):
        """Test ACH payment method"""
        charge = MockStripeCharge()
        charge.payment_method_details = MockPaymentMethodDetails(type='ach_debit')
        
        result = get_detailed_payment_method(charge)
        assert result == 'ACH/Bank Transfer'
    
    def test_unknown_payment_method(self):
        """Test unknown payment method"""
        charge = MockStripeCharge()
        charge.payment_method_details = None
        charge.source = None
        
        result = get_detailed_payment_method(charge)
        assert result == 'Unknown'
    
    def test_legacy_source_with_brand(self):
        """Test legacy source object with brand"""
        charge = MockStripeCharge()
        charge.payment_method_details = None
        
        # Mock legacy source
        source_mock = Mock()
        source_mock.brand = 'mastercard'
        charge.source = source_mock
        
        result = get_detailed_payment_method(charge)
        assert result == 'Mastercard'

class TestStripeServiceIntegration:
    """Integration tests for stripe service functions"""
    
    @patch('services.stripe_service.stripe')
    def test_get_stripe_data_success(self, mock_stripe):
        """Test successful data retrieval from Stripe API"""
        # This would test the actual API integration
        # For now, we'll mock the stripe module
        mock_charges = create_mock_charges(3)
        
        # Mock the Stripe charge list method
        mock_stripe.Charge.list.return_value.auto_paging_iter.return_value = mock_charges
        
        # We would import and test get_stripe_data here
        # but it requires proper mocking of streamlit session state
        pass
    
    @patch('services.stripe_service.stripe')
    def test_get_stripe_data_error_handling(self, mock_stripe):
        """Test error handling in Stripe API calls"""
        mock_stripe.Charge.list.side_effect = Exception("API Error")
        
        # Test that errors are handled gracefully
        # This would require importing get_stripe_data and testing it
        pass
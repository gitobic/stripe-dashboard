import stripe
import streamlit as st
from datetime import datetime
from services.cache_service import cache_stripe_data
from config.settings import STRIPE_SECRET_KEY, CUSTOMER_CACHE_TTL_SECONDS

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

@cache_stripe_data(ttl_seconds=300)
def get_stripe_data(start_date, end_date):
    """Fetch Stripe data for the given date range with auto-pagination"""
    try:
        charges_data = []
        # Use auto-pagination to get ALL charges in date range
        for charge in stripe.Charge.list(
            created={
                'gte': int(start_date.timestamp()),
                'lte': int(end_date.timestamp())
            },
            expand=['data.customer']
        ).auto_paging_iter():
            charges_data.append(charge)
        
        return charges_data
    except Exception as e:
        st.error(f"Error fetching Stripe data: {str(e)}")
        return []

def filter_charges_data(charges_data, status_filter, min_amount, max_amount):
    """Filter charges data based on user selections"""
    if not charges_data:
        return []
    
    # If no status filter selected, include all statuses
    if not status_filter:
        status_filter = [
            # Basic statuses
            "succeeded", "failed", "pending", "canceled",
            # Refund statuses  
            "refunded", "refund_pending", "partially_refunded",
            # Dispute statuses
            "disputed", "lost", "won", "dispute_under_review", 
            "dispute_needs_response", "closed", 
            "inquiry_under_review", "inquiry_needs_response"
        ]
    
    filtered_data = []
    for charge in charges_data:
        # Status filter
        if charge.status not in status_filter:
            continue
        
        # Amount filter (convert from cents to dollars)
        amount_dollars = charge.amount / 100
        if amount_dollars < min_amount or amount_dollars > max_amount:
            continue
        
        filtered_data.append(charge)
    
    return filtered_data

def get_data_date_range():
    """Get the date range of available data to set smart defaults"""
    try:
        # Get the most recent charge
        recent_charges = stripe.Charge.list(limit=1)
        if not recent_charges.data:
            return None, None
        
        newest_date = datetime.fromtimestamp(recent_charges.data[0].created)
        
        # Get the oldest charges (approximate by going back far and taking the oldest)
        old_charges = stripe.Charge.list(
            created={'lte': int(newest_date.timestamp())},
            limit=100
        )
        
        if old_charges.data:
            oldest_date = datetime.fromtimestamp(min(charge.created for charge in old_charges.data))
            return oldest_date, newest_date
        
        return newest_date, newest_date
    except Exception:
        return None, None

@cache_stripe_data(ttl_seconds=CUSTOMER_CACHE_TTL_SECONDS)  # Cache customers longer
def get_customers_data():
    """Fetch customer data from Stripe with auto-pagination"""
    try:
        customers_data = []
        # Use auto-pagination to get ALL customers
        for customer in stripe.Customer.list().auto_paging_iter():
            customers_data.append(customer)
        return customers_data
    except Exception as e:
        st.error(f"Error fetching customers data: {str(e)}")
        return []

def get_customer_payment_history(customer_id, limit=10):
    """Get payment history for a specific customer"""
    try:
        charges = stripe.Charge.list(
            customer=customer_id,
            limit=limit,
            expand=['data.payment_method']
        )
        return charges.data
    except Exception as e:
        st.error(f"Error fetching payment history: {str(e)}")
        return []

def get_customer_subscriptions(customer_id):
    """Get subscriptions for a specific customer"""
    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            expand=['data.items.data.price.product']
        )
        return subscriptions.data
    except Exception as e:
        st.error(f"Error fetching customer subscriptions: {str(e)}")
        return []

@cache_stripe_data(ttl_seconds=CUSTOMER_CACHE_TTL_SECONDS)
def get_all_subscriptions():
    """Fetch all subscription data from Stripe with auto-pagination"""
    try:
        subscriptions_data = []
        # Use auto-pagination to get ALL subscriptions with related data expanded
        for subscription in stripe.Subscription.list(
            expand=['data.customer', 'data.items.data.price.product']
        ).auto_paging_iter():
            subscriptions_data.append(subscription)
        return subscriptions_data
    except Exception as e:
        st.error(f"Error fetching subscriptions data: {str(e)}")
        return []

def get_detailed_payment_method(charge):
    """Get detailed payment method info including card brands"""
    if hasattr(charge, 'payment_method_details') and charge.payment_method_details:
        pm_details = charge.payment_method_details
        
        if pm_details.type == 'card' and hasattr(pm_details, 'card') and pm_details.card:
            card_info = pm_details.card
            # Get card brand (visa, mastercard, amex, etc.)
            if hasattr(card_info, 'brand') and card_info.brand:
                brand = card_info.brand.title()
                # Add wallet info if available (Apple Pay, Google Pay, etc.)
                if hasattr(card_info, 'wallet') and card_info.wallet:
                    wallet_type = card_info.wallet.type
                    if wallet_type == 'apple_pay':
                        return f"{brand} (Apple Pay)"
                    elif wallet_type == 'google_pay':
                        return f"{brand} (Google Pay)"
                    elif wallet_type == 'samsung_pay':
                        return f"{brand} (Samsung Pay)"
                    else:
                        return f"{brand} ({wallet_type.replace('_', ' ').title()})"
                return brand
            else:
                return 'Card'
        elif pm_details.type == 'ach_debit':
            return 'ACH/Bank Transfer'
        elif pm_details.type == 'sepa_debit':
            return 'SEPA Direct Debit'
        else:
            return pm_details.type.replace('_', ' ').title()
    
    # Fallback for older charges without payment_method_details
    if hasattr(charge, 'source') and charge.source:
        if hasattr(charge.source, 'brand') and charge.source.brand:
            return charge.source.brand.title()
        elif hasattr(charge.source, 'object') and charge.source.object == 'card':
            return 'Card'
    
    return 'Unknown'
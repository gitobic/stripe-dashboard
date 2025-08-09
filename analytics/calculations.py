import stripe
from datetime import datetime, timedelta
from services.stripe_service import get_all_subscriptions
from utils.helpers import get_subscription_items_data

def calculate_mrr_arr(subscriptions_data):
    """Calculate Monthly and Annual Recurring Revenue"""
    mrr = 0
    arr = 0
    debug_info = []
    
    for sub in subscriptions_data:
        if sub.status in ['active', 'trialing']:
            # Get subscription items - items is a method, not a property
            # Use the helper function to get items
            items_data = get_subscription_items_data(sub)
            
            debug_info.append(f"Sub {sub.id[-8:]}: status={sub.status}")
            debug_info.append(f"  - Items count: {len(items_data)}")
            
            if items_data and len(items_data) > 0:
                item = items_data[0]
                debug_info.append(f"  - First item: {type(item)}")
                
                # Try to get price from item (handle both objects and dicts)
                price = None
                if hasattr(item, 'price'):  # Real Stripe item object
                    price = item.price
                elif isinstance(item, dict) and 'price' in item:  # Our fake dict structure
                    price = item['price']
                
                if price:
                    debug_info.append(f"  - Price object: {type(price)}")
                    
                    # Get price details - price might be an ID that needs to be fetched
                    if isinstance(price, str):
                        try:
                            price = stripe.Price.retrieve(price)
                            debug_info.append(f"  - Retrieved price: {type(price)}")
                        except:
                            debug_info.append(f"  - Failed to retrieve price {price}")
                            continue
                    
                    # Get quantity (handle both objects and dicts)
                    if hasattr(item, 'quantity'):
                        quantity = item.quantity
                    elif isinstance(item, dict) and 'quantity' in item:
                        quantity = item['quantity']
                    else:
                        quantity = 1
                    debug_info.append(f"  - Quantity: {quantity}")
                    
                    # Try different ways to get amount (handle both Price and Plan objects)
                    amount = 0
                    if hasattr(price, 'unit_amount') and price.unit_amount:
                        amount = (price.unit_amount / 100) * quantity
                        debug_info.append(f"  - Amount (unit_amount): ${amount}")
                    elif hasattr(price, 'amount') and price.amount:  # Legacy plan
                        amount = (price.amount / 100) * quantity
                        debug_info.append(f"  - Amount (plan amount): ${amount}")
                    elif hasattr(price, 'unit_amount_decimal'):
                        amount = (float(price.unit_amount_decimal) / 100) * quantity
                        debug_info.append(f"  - Amount (decimal): ${amount}")
                    else:
                        debug_info.append(f"  - No amount found in price")
                    
                    # Handle both new recurring and legacy interval
                    interval = None
                    if hasattr(price, 'recurring') and price.recurring:
                        interval = price.recurring.interval
                        debug_info.append(f"  - Interval (recurring): {interval}")
                    elif hasattr(price, 'interval'):  # Legacy plan
                        interval = price.interval
                        debug_info.append(f"  - Interval (plan): {interval}")
                    else:
                        debug_info.append(f"  - No interval found")
                    
                    if interval:
                        if interval == 'month':
                            mrr += amount
                        elif interval == 'year':
                            arr += amount
                            mrr += amount / 12  # Convert annual to monthly
                        elif interval == 'week':
                            mrr += amount * 4.33  # ~4.33 weeks per month
                        elif interval == 'day':
                            mrr += amount * 30  # 30 days per month
                else:
                    debug_info.append(f"  - No price found in item")
            else:
                debug_info.append(f"  - No items found")
    
    arr = mrr * 12  # Total ARR including converted subscriptions
    return mrr, arr

def calculate_churn_metrics(subscriptions_data):
    """Calculate churn rate and trial conversion metrics"""
    total_subs = len(subscriptions_data)
    active_subs = len([s for s in subscriptions_data if s.status == 'active'])
    trialing_subs = len([s for s in subscriptions_data if s.status == 'trialing'])
    canceled_subs = len([s for s in subscriptions_data if s.status == 'canceled'])
    
    # Calculate churn rate (canceled / total)
    churn_rate = (canceled_subs / total_subs * 100) if total_subs > 0 else 0
    
    # Calculate trial conversion rate (would need historical data for accuracy)
    # For now, we'll show current trialing vs active ratio
    trial_conversion_rate = (active_subs / (active_subs + trialing_subs) * 100) if (active_subs + trialing_subs) > 0 else 0
    
    return {
        'total_subscriptions': total_subs,
        'active_subscriptions': active_subs,
        'trialing_subscriptions': trialing_subs,
        'canceled_subscriptions': canceled_subs,
        'churn_rate': round(churn_rate, 2),
        'trial_conversion_rate': round(trial_conversion_rate, 2)
    }

def calculate_customer_lifetime_value(customer_id, transactions_data):
    """Calculate estimated Customer Lifetime Value"""
    try:
        # Filter transactions for this specific customer
        customer_transactions = [
            charge for charge in transactions_data 
            if charge.customer and (
                (hasattr(charge.customer, 'id') and charge.customer.id == customer_id) or
                charge.customer == customer_id
            ) and charge.status == 'succeeded'
        ]
        
        if not customer_transactions:
            return 0.0
        
        # Calculate total revenue from this customer
        total_revenue = sum(charge.amount / 100 for charge in customer_transactions)
        
        # Calculate transaction frequency (transactions per month)
        if len(customer_transactions) < 2:
            return total_revenue  # Single transaction customer
        
        # Get date range of customer activity
        transaction_dates = [datetime.fromtimestamp(charge.created) for charge in customer_transactions]
        earliest_date = min(transaction_dates)
        latest_date = max(transaction_dates)
        
        # Calculate months active
        months_active = max(1, (latest_date - earliest_date).days / 30.44)  # Average days per month
        
        # Calculate average monthly value
        monthly_value = total_revenue / months_active
        
        # Simple CLV estimation: Average Monthly Value * Estimated Lifespan (24 months)
        # This is a simplified model - in practice you'd want more sophisticated prediction
        estimated_clv = monthly_value * 24
        
        return round(estimated_clv, 2)
        
    except Exception as e:
        return 0.0

def forecast_revenue(transactions_data, months_ahead=3):
    """Simple revenue forecasting based on historical trends"""
    try:
        if not transactions_data:
            return []
        
        # Group transactions by month
        monthly_data = {}
        for charge in transactions_data:
            if charge.status == 'succeeded':
                month_key = datetime.fromtimestamp(charge.created).strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = 0
                monthly_data[month_key] += charge.amount / 100
        
        if len(monthly_data) < 2:
            # Not enough data for forecasting
            return []
        
        # Calculate simple trend
        months = sorted(monthly_data.keys())
        revenues = [monthly_data[month] for month in months]
        
        # Simple linear trend calculation
        n = len(revenues)
        if n < 3:
            avg_growth = 0  # No growth if less than 3 data points
        else:
            # Calculate average month-over-month growth rate
            growth_rates = []
            for i in range(1, len(revenues)):
                if revenues[i-1] > 0:
                    growth_rate = (revenues[i] - revenues[i-1]) / revenues[i-1]
                    growth_rates.append(growth_rate)
            
            avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        
        # Generate forecasts
        last_month_revenue = revenues[-1]
        forecasts = []
        
        for i in range(1, months_ahead + 1):
            # Apply average growth rate with some dampening for conservatism
            dampened_growth = avg_growth * 0.8  # 20% more conservative
            forecasted_revenue = last_month_revenue * (1 + dampened_growth) ** i
            
            # Add forecast date
            last_date = datetime.strptime(months[-1], '%Y-%m')
            forecast_date = datetime(
                last_date.year + (last_date.month + i - 1) // 12,
                (last_date.month + i - 1) % 12 + 1,
                1
            )
            
            forecasts.append({
                'month': forecast_date.strftime('%Y-%m'),
                'forecasted_revenue': round(forecasted_revenue, 2),
                'confidence': max(0.5, 0.9 - (i * 0.1))  # Decreasing confidence
            })
        
        return forecasts
        
    except Exception as e:
        return []

def calculate_stripe_fees(transactions_data):
    """Calculate detailed Stripe fee analysis"""
    if not transactions_data:
        return {
            'total_fees': 0,
            'total_revenue': 0,
            'fee_percentage': 0,
            'transaction_count': 0,
            'average_fee_per_transaction': 0,
            'fees_by_payment_method': {},
            'recommendations': []
        }
    
    total_fees = 0
    total_revenue = 0
    transaction_count = 0
    fees_by_method = {}
    
    for charge in transactions_data:
        if charge.status == 'succeeded':
            transaction_count += 1
            amount = charge.amount / 100  # Convert from cents
            total_revenue += amount
            
            # Estimate Stripe fees (this is approximate - real fees vary)
            # Standard rates: 2.9% + 30¢ for online cards
            base_fee = amount * 0.029 + 0.30
            
            # Adjust for payment method (rough estimates)
            payment_method = get_detailed_payment_method(charge)
            
            if 'amex' in payment_method.lower():
                # American Express typically has higher fees
                estimated_fee = amount * 0.035 + 0.30
            elif 'ach' in payment_method.lower() or 'bank' in payment_method.lower():
                # ACH/Bank transfers have lower fees
                estimated_fee = min(5.00, amount * 0.008)  # 0.8% capped at $5
            elif 'international' in payment_method.lower():
                # International cards have higher fees
                estimated_fee = amount * 0.039 + 0.30
            else:
                # Standard card processing
                estimated_fee = base_fee
            
            total_fees += estimated_fee
            
            # Track fees by payment method
            if payment_method not in fees_by_method:
                fees_by_method[payment_method] = {'total_fees': 0, 'count': 0, 'revenue': 0}
            
            fees_by_method[payment_method]['total_fees'] += estimated_fee
            fees_by_method[payment_method]['count'] += 1
            fees_by_method[payment_method]['revenue'] += amount
    
    # Calculate percentages and averages
    fee_percentage = (total_fees / total_revenue * 100) if total_revenue > 0 else 0
    avg_fee_per_transaction = total_fees / transaction_count if transaction_count > 0 else 0
    
    # Generate recommendations
    recommendations = []
    if fee_percentage > 3.5:
        recommendations.append("Consider negotiating lower rates with Stripe for your volume")
    if any('amex' in method.lower() for method in fees_by_method.keys()):
        recommendations.append("American Express transactions have higher fees - consider surcharging")
    if transaction_count > 100:
        recommendations.append("With your transaction volume, you may qualify for custom pricing")
    
    return {
        'total_fees': round(total_fees, 2),
        'total_revenue': round(total_revenue, 2),
        'fee_percentage': round(fee_percentage, 2),
        'transaction_count': transaction_count,
        'average_fee_per_transaction': round(avg_fee_per_transaction, 2),
        'fees_by_payment_method': fees_by_method,
        'recommendations': recommendations
    }

# Helper function import
def get_detailed_payment_method(charge):
    """Get detailed payment method info including card brands - imported from stripe_service"""
    from services.stripe_service import get_detailed_payment_method as _get_detailed_payment_method
    return _get_detailed_payment_method(charge)
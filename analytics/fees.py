from services.stripe_service import get_detailed_payment_method

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
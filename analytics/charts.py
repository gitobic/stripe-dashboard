import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.formatters import get_product_info_for_chart
from services.stripe_service import get_detailed_payment_method

def create_revenue_chart(charges_data):
    """Create a revenue chart from charges data"""
    if not charges_data:
        return go.Figure()
    
    df = pd.DataFrame([{
        'date': datetime.fromtimestamp(charge.created).date(),
        'amount': charge.amount / 100,  # Convert from cents
        'currency': charge.currency,
        'status': charge.status
    } for charge in charges_data])
    
    daily_revenue = df.groupby('date')['amount'].sum().reset_index()
    
    fig = px.line(
        daily_revenue, 
        x='date', 
        y='amount',
        title='Daily Revenue',
        labels={'amount': 'Revenue ($)', 'date': 'Date'}
    )
    
    return fig

def create_product_chart(charges_data):
    """Create a product breakdown chart from charges data"""
    if not charges_data:
        return go.Figure()
    
    df = pd.DataFrame([{
        'product': get_product_info_for_chart(charge),
        'amount': charge.amount / 100,  # Convert from cents
    } for charge in charges_data])
    
    product_revenue = df.groupby('product')['amount'].sum().reset_index()
    product_revenue = product_revenue.sort_values('amount', ascending=False)
    
    fig = px.bar(
        product_revenue, 
        x='product', 
        y='amount',
        title='Revenue by Product',
        labels={'amount': 'Revenue ($)', 'product': 'Product'}
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_payment_method_chart(charges_data):
    """Create a payment method breakdown chart from charges data"""
    if not charges_data:
        return go.Figure()
    
    df = pd.DataFrame([{
        'payment_method': get_detailed_payment_method(charge),
        'amount': charge.amount / 100,  # Convert from cents
    } for charge in charges_data])
    
    payment_revenue = df.groupby('payment_method')['amount'].sum().reset_index()
    payment_revenue = payment_revenue.sort_values('amount', ascending=False)
    
    # Create a pie chart for payment methods
    fig = px.pie(
        payment_revenue, 
        values='amount', 
        names='payment_method',
        title='Revenue by Payment Method & Card Brand'
    )
    
    return fig

def create_subscription_charts(subscriptions_data):
    """Create subscription-related charts"""
    if not subscriptions_data:
        return go.Figure(), go.Figure()
    
    # Status breakdown chart
    status_counts = {}
    for sub in subscriptions_data:
        status = sub.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    status_df = pd.DataFrame([
        {'status': status, 'count': count}
        for status, count in status_counts.items()
    ])
    
    status_fig = px.pie(
        status_df,
        values='count',
        names='status',
        title='Subscription Status Breakdown'
    )
    
    # Revenue by plan chart
    plan_revenue = {}
    for sub in subscriptions_data:
        if sub.status in ['active', 'trialing']:
            plan_name = get_subscription_plan_name(sub)
            amount = get_subscription_amount(sub)
            
            if plan_name not in plan_revenue:
                plan_revenue[plan_name] = 0
            plan_revenue[plan_name] += amount
    
    plan_df = pd.DataFrame([
        {'plan': plan, 'revenue': revenue}
        for plan, revenue in plan_revenue.items()
    ])
    
    if not plan_df.empty:
        plan_fig = px.bar(
            plan_df,
            x='plan',
            y='revenue',
            title='Monthly Revenue by Subscription Plan'
        )
        plan_fig.update_xaxes(tickangle=45)
    else:
        plan_fig = go.Figure()
    
    return status_fig, plan_fig

# Helper functions for subscription charts
def get_subscription_plan_name(subscription):
    """Get the plan name from a subscription"""
    try:
        # Get subscription items
        from utils.helpers import get_subscription_items_data
        items = get_subscription_items_data(subscription)
        
        if items and len(items) > 0:
            item = items[0]
            
            # Try to get price
            price = None
            if hasattr(item, 'price'):
                price = item.price
            elif isinstance(item, dict) and 'price' in item:
                price = item['price']
            
            if price:
                # Try to get product name from price
                if hasattr(price, 'product') and price.product:
                    if hasattr(price.product, 'name'):
                        return price.product.name
                    elif isinstance(price.product, str):
                        return price.product
                
                # Fallback to price nickname or ID
                if hasattr(price, 'nickname') and price.nickname:
                    return price.nickname
                elif hasattr(price, 'id'):
                    return f"Plan ({price.id[-8:]})"
        
        return f"Plan ({subscription.id[-8:]})"
        
    except Exception:
        return "Unknown Plan"

def get_subscription_amount(subscription):
    """Get the monthly amount from a subscription"""
    try:
        from utils.helpers import get_subscription_items_data
        items = get_subscription_items_data(subscription)
        
        if items and len(items) > 0:
            item = items[0]
            
            # Try to get price
            price = None
            if hasattr(item, 'price'):
                price = item.price
            elif isinstance(item, dict) and 'price' in item:
                price = item['price']
            
            if price:
                # Get quantity
                quantity = 1
                if hasattr(item, 'quantity'):
                    quantity = item.quantity
                elif isinstance(item, dict) and 'quantity' in item:
                    quantity = item['quantity']
                
                # Get amount
                if hasattr(price, 'unit_amount') and price.unit_amount:
                    amount = (price.unit_amount / 100) * quantity
                elif hasattr(price, 'amount') and price.amount:
                    amount = (price.amount / 100) * quantity
                else:
                    return 0
                
                # Convert to monthly if needed
                interval = None
                if hasattr(price, 'recurring') and price.recurring:
                    interval = price.recurring.interval
                elif hasattr(price, 'interval'):
                    interval = price.interval
                
                if interval == 'year':
                    return amount / 12
                elif interval == 'week':
                    return amount * 4.33
                elif interval == 'day':
                    return amount * 30
                else:  # month or unknown
                    return amount
        
        return 0
        
    except Exception:
        return 0
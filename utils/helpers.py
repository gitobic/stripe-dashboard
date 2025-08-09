def get_subscription_items_data(subscription):
    """Extract subscription items data from a subscription object"""
    try:
        items = []
        
        if hasattr(subscription, 'items') and subscription.items:
            if hasattr(subscription.items, 'data'):
                # It's a ListObject with data
                items = subscription.items.data
            elif hasattr(subscription.items, '__iter__'):
                # It's directly iterable
                items = list(subscription.items)
        
        return items
        
    except Exception as e:
        return []

def get_subscription_amount(subscription):
    """Get the amount from a subscription"""
    try:
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
                    return (price.unit_amount / 100) * quantity
                elif hasattr(price, 'amount') and price.amount:
                    return (price.amount / 100) * quantity
        
        return 0.0
        
    except Exception:
        return 0.0

def get_subscription_interval(subscription):
    """Get the billing interval from a subscription"""
    try:
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
                # Handle both new recurring and legacy interval
                if hasattr(price, 'recurring') and price.recurring:
                    return price.recurring.interval
                elif hasattr(price, 'interval'):
                    return price.interval
        
        return 'month'  # Default fallback
        
    except Exception:
        return 'month'

def get_subscription_status_info(subscription):
    """Get detailed status information from a subscription"""
    status_colors = {
        'active': 'green',
        'trialing': 'blue',
        'past_due': 'orange',
        'canceled': 'red',
        'unpaid': 'red',
        'incomplete': 'orange',
        'incomplete_expired': 'red'
    }
    
    status_descriptions = {
        'active': 'Active subscription',
        'trialing': 'In trial period',
        'past_due': 'Payment overdue',
        'canceled': 'Subscription canceled',
        'unpaid': 'Payment failed',
        'incomplete': 'Setup incomplete',
        'incomplete_expired': 'Setup expired'
    }
    
    status = subscription.status
    return {
        'status': status,
        'color': status_colors.get(status, 'gray'),
        'description': status_descriptions.get(status, 'Unknown status')
    }

def get_subscription_plan_name(subscription):
    """Get the plan name from a subscription"""
    try:
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
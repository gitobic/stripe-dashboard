def get_product_info_for_chart(charge):
    """Get product info for charts - same logic as display but separate function"""
    # Try to get from metadata first
    if hasattr(charge, 'metadata') and charge.metadata:
        if 'product_name' in charge.metadata:
            return charge.metadata['product_name']
        elif 'product' in charge.metadata:
            return charge.metadata['product']
        elif 'item_name' in charge.metadata:
            return charge.metadata['item_name']
    
    # Try to get from description
    if hasattr(charge, 'description') and charge.description:
        desc = charge.description
        if not desc.lower().startswith('payment for'):
            return desc
    
    # Try statement descriptor
    if hasattr(charge, 'statement_descriptor') and charge.statement_descriptor:
        return charge.statement_descriptor
    
    return 'Payment'

def get_customer_name_for_export(charge):
    """Get customer name for export - similar to display function"""
    if not charge.customer:
        return 'Guest'
    
    # If customer is expanded, get the name
    if hasattr(charge.customer, 'name') and charge.customer.name:
        return charge.customer.name
    elif hasattr(charge.customer, 'email') and charge.customer.email:
        return charge.customer.email
    elif isinstance(charge.customer, str):
        return charge.customer  # Full ID for export
    else:
        return 'Guest'
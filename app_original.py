import streamlit as st
import stripe
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
from io import BytesIO
import time
from functools import wraps

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

st.set_page_config(
    page_title="Stripe Dashboard",
    page_icon="💳",
    layout="wide"
)

def cache_stripe_data(ttl_seconds=300):  # 5-minute cache
    """Decorator to cache Stripe API calls and reduce redundant requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Check if data exists in session state cache
            if cache_key in st.session_state:
                cached_data, timestamp = st.session_state[cache_key]
                if time.time() - timestamp < ttl_seconds:
                    return cached_data
            
            # Fetch fresh data and cache it
            result = func(*args, **kwargs)
            st.session_state[cache_key] = (result, time.time())
            return result
        return wrapper
    return decorator

def clear_stripe_cache():
    """Clear all cached Stripe data"""
    cache_keys_to_remove = [key for key in st.session_state.keys() if key.startswith(('get_stripe_data_', 'get_customers_data_', 'get_all_subscriptions_'))]
    for key in cache_keys_to_remove:
        del st.session_state[key]

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

@cache_stripe_data(ttl_seconds=600)  # Cache customers longer
def get_customers_data():
    """Fetch customer data from Stripe with auto-pagination"""
    try:
        customers_data = []
        # Use auto-pagination to get ALL customers
        for customer in stripe.Customer.list().auto_paging_iter():
            customers_data.append(customer)
        
        return customers_data
    except Exception as e:
        st.error(f"Error fetching customer data: {str(e)}")
        return []

def get_customer_payment_history(customer_id, limit=10):
    """Get payment history for a specific customer"""
    try:
        charges = stripe.Charge.list(
            customer=customer_id,
            limit=limit,
            expand=['data.customer']
        )
        return charges.data
    except Exception as e:
        st.error(f"Error fetching customer payment history: {str(e)}")
        return []

def get_customer_subscriptions(customer_id):
    """Get subscription data for a specific customer"""
    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            limit=10
        )
        return subscriptions.data
    except Exception as e:
        st.error(f"Error fetching customer subscriptions: {str(e)}")
        return []

@cache_stripe_data(ttl_seconds=600)  # Cache subscriptions longer
def get_all_subscriptions():
    """Get all subscription data from Stripe with auto-pagination and better expansion"""
    try:
        subscriptions_data = []
        # Use auto-pagination and expand all needed relationships
        for subscription in stripe.Subscription.list(
            expand=[
                'data.customer', 
                'data.items.data.price',
                'data.default_payment_method'
            ]
        ).auto_paging_iter():
            subscriptions_data.append(subscription)
        
        return subscriptions_data
    except Exception as e:
        st.error(f"Error fetching subscriptions: {str(e)}")
        return []

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
    
    # Optional: Show debug info (comment out for production)
    # if debug_info:
    #     st.write("**Debug - MRR Calculation:**")
    #     for info in debug_info:
    #         st.write(info)
    
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
        'churn_rate': churn_rate,
        'trial_conversion_rate': trial_conversion_rate
    }

def render_customers_dashboard():
    """Render the customers dashboard"""
    st.header("👥 Customers")
    
    # Control Panel Header
    st.subheader("👥 Customer Controls")
    
    # Customer filters in organized layout
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.write("**Customer Status:**")
        customer_status = st.selectbox(
            "Filter by Status",
            ["All", "Active", "Inactive"],
            key="cust_status_filter"
        )
    
    with col2:
        st.write("**Search & Tags:**")
        search_term = st.text_input("Search by name or email", key="cust_search")
        # Tag filter
        available_tags = list(load_tags_and_notes()["tag_definitions"].keys())
        tag_filter = st.selectbox(
            "Filter by Tag",
            ["All Tags"] + available_tags,
            key="cust_tag_filter"
        )
    
    with col3:
        st.write("**Quick Actions:**")
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            if st.button("🔄 Refresh Customer Data", key="cust_refresh"):
                st.rerun()
        
        with quick_col2:
            # Placeholder for CSV export button - will be functional after data load
            csv_button_placeholder = st.empty()
        
        with quick_col3:
            # Placeholder for Excel export button - will be functional after data load
            excel_button_placeholder = st.empty()
    
    st.markdown("---")
    
    # Fetch customers
    with st.spinner('Loading customers...'):
        customers_data = get_customers_data()
    
    if customers_data:
        # Filter customers based on search and tags
        filtered_customers = []
        for customer in customers_data:
            # Search filter
            if search_term:
                customer_text = f"{customer.name or ''} {customer.email or ''}".lower()
                if search_term.lower() not in customer_text:
                    continue
            
            # Tag filter
            if tag_filter != "All Tags":
                customer_tags = get_customer_tags(customer.id)
                if tag_filter not in customer_tags:
                    continue
            
            filtered_customers.append(customer)
        
        # Customer summary metrics
        total_customers = len(filtered_customers)
        active_customers = sum(1 for c in filtered_customers if getattr(c, 'delinquent', False) == False)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Customers", total_customers)
        with col2:
            st.metric("Active Customers", active_customers)
        with col3:
            if total_customers > 0:
                st.metric("Active Rate", f"{(active_customers/total_customers)*100:.1f}%")
        
        st.markdown("---")
        
        # Customer list
        st.subheader("Customer List")
        
        # Create customer DataFrame
        customer_df = pd.DataFrame([{
            'Name': customer.name or 'N/A',
            'Email': customer.email or 'N/A',
            'Created': datetime.fromtimestamp(customer.created).strftime('%Y-%m-%d'),
            'Status': 'Active' if not getattr(customer, 'delinquent', False) else 'Delinquent',
            'Tags': ', '.join(get_customer_tags(customer.id)) or 'None',
            'Customer ID': customer.id
        } for customer in filtered_customers])
        
        # Display customers table with selection
        selected_customer = st.selectbox(
            "Select customer for details:",
            options=['None'] + [f"{row['Name']} ({row['Email']})" for _, row in customer_df.iterrows()],
            key="customer_selector"
        )
        
        st.dataframe(customer_df, use_container_width=True)
        
        # Populate Quick Actions export buttons with actual data
        with csv_button_placeholder.container():
            # CSV export
            csv_data = customer_df.to_csv(index=False)
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"stripe_customers_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
                key="cust_csv_export"
            )
        
        with excel_button_placeholder.container():
            # Excel export
            from io import BytesIO
            excel_buffer = BytesIO()
            customer_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="📊 Export Excel", 
                data=excel_data,
                file_name=f"stripe_customers_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="cust_excel_export"
            )
        
        # Customer detail view
        if selected_customer != 'None':
            customer_index = customer_df.index[customer_df.apply(lambda row: f"{row['Name']} ({row['Email']})" == selected_customer, axis=1)].tolist()
            if customer_index:
                selected_customer_data = filtered_customers[customer_index[0]]
                render_customer_detail(selected_customer_data)
    
    else:
        st.info("No customers found")

def render_customer_detail(customer):
    """Render detailed view for a specific customer"""
    st.markdown("---")
    st.subheader(f"Customer Details: {customer.name or customer.email or customer.id}")
    
    # Customer info with tags and notes
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.write("**Contact Information:**")
        st.write(f"Name: {customer.name or 'N/A'}")
        st.write(f"Email: {customer.email or 'N/A'}")
        st.write(f"Phone: {getattr(customer, 'phone', 'N/A') or 'N/A'}")
        st.write(f"Created: {datetime.fromtimestamp(customer.created).strftime('%Y-%m-%d %H:%M')}")
    
    with col2:
        st.write("**Account Status:**")
        st.write(f"Delinquent: {'Yes' if getattr(customer, 'delinquent', False) else 'No'}")
        st.write(f"Balance: ${getattr(customer, 'balance', 0) / 100:.2f}")
        st.write(f"Currency: {(getattr(customer, 'currency', 'usd') or 'usd').upper()}")
    
    with col3:
        st.write("**Additional Info:**")
        # Show created date
        if hasattr(customer, 'created'):
            created_date = datetime.fromtimestamp(customer.created).strftime('%Y-%m-%d')
            st.write(f"Customer since: {created_date}")
        
        # Show customer description if available
        if hasattr(customer, 'description') and customer.description:
            st.write(f"Description: {customer.description}")
        else:
            st.write("No description available")
    
    # Payment history
    st.subheader("Payment History")
    with st.spinner('Loading payment history...'):
        payment_history = get_customer_payment_history(customer.id)
    
    if payment_history:
        history_df = pd.DataFrame([{
            'Date': datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M'),
            'Amount': f"${charge.amount / 100:.2f}",
            'Status': charge.status.title(),
            'Product': get_product_info_for_chart(charge),
            'Payment Method': get_detailed_payment_method(charge)
        } for charge in payment_history])
        
        st.dataframe(history_df, use_container_width=True)
        
        # Payment summary
        total_paid = sum(charge.amount for charge in payment_history if charge.status == 'succeeded') / 100
        failed_payments = sum(1 for charge in payment_history if charge.status == 'failed')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Paid", f"${total_paid:.2f}")
        with col2:
            st.metric("Total Payments", len(payment_history))
        with col3:
            st.metric("Failed Payments", failed_payments)
    else:
        st.info("No payment history found for this customer")
    
    # Subscriptions
    st.subheader("Subscriptions")
    with st.spinner('Loading subscriptions...'):
        subscriptions = get_customer_subscriptions(customer.id)
    
    if subscriptions:
        subs_df = pd.DataFrame([{
            'Status': sub.status.title(),
            'Start Date': datetime.fromtimestamp(sub.start_date).strftime('%Y-%m-%d') if hasattr(sub, 'start_date') and sub.start_date else 'N/A',
            'Current Period End': datetime.fromtimestamp(sub.current_period_end).strftime('%Y-%m-%d') if hasattr(sub, 'current_period_end') and sub.current_period_end else 'N/A',
            'Amount': f"${(sub.items.data[0].price.unit_amount if hasattr(sub, 'items') and sub.items.data and sub.items.data[0].price.unit_amount else 0) / 100:.2f}",
            'Interval': f"{sub.items.data[0].price.recurring.interval if hasattr(sub, 'items') and sub.items.data and sub.items.data[0].price.recurring else 'N/A'}",
            'Subscription ID': sub.id
        } for sub in subscriptions])
        
        st.dataframe(subs_df, use_container_width=True)
    else:
        st.info("No subscriptions found for this customer")

def render_subscriptions_dashboard():
    """Render the subscriptions dashboard"""
    st.header("🔄 Subscriptions")
    
    # Control Panel Header
    st.subheader("🔄 Subscription Controls")
    
    # Subscription filters in organized layout
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.write("**Subscription Status:**")
        status_filter = st.multiselect(
            "Filter by Status",
            ["active", "trialing", "canceled", "past_due", "incomplete"],
            default=["active", "trialing"],
            key="sub_status_filter"
        )
    
    with col2:
        st.write("**Plan & Period:**")
        plan_filter = st.selectbox(
            "Plan Type",
            ["All Plans", "Monthly", "Annual", "Weekly"],
            key="sub_plan_filter"
        )
        created_days = st.selectbox(
            "Created Within",
            ["All Time", "Last 30 Days", "Last 90 Days", "Last Year"],
            key="sub_created_filter"
        )
    
    with col3:
        st.write("**Quick Actions:**")
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            if st.button("🔄 Refresh Subscription Data", key="sub_refresh"):
                st.rerun()
        
        with quick_col2:
            # Placeholder for CSV export button - will be functional after data load
            csv_button_placeholder = st.empty()
        
        with quick_col3:
            # Placeholder for Excel export button - will be functional after data load
            excel_button_placeholder = st.empty()
    
    st.markdown("---")
    
    # Fetch subscriptions
    with st.spinner('Loading subscriptions...'):
        all_subscriptions = get_all_subscriptions()
    
    # Show subscription count
    if all_subscriptions:
        st.info(f"Found {len(all_subscriptions)} total subscriptions")
    
    if all_subscriptions:
        # Filter subscriptions
        filtered_subs = []
        cutoff_date = None
        if created_days == "Last 30 Days":
            cutoff_date = datetime.now() - timedelta(days=30)
        elif created_days == "Last 90 Days":
            cutoff_date = datetime.now() - timedelta(days=90)
        elif created_days == "Last Year":
            cutoff_date = datetime.now() - timedelta(days=365)
        
        for sub in all_subscriptions:
            # Status filter
            if sub.status not in status_filter:
                continue
            
            # Plan type filter
            if plan_filter != "All Plans":
                interval = get_subscription_interval(sub)
                if plan_filter == "Monthly" and interval != "month":
                    continue
                elif plan_filter == "Annual" and interval != "year":
                    continue
                elif plan_filter == "Weekly" and interval != "week":
                    continue
            
            # Date filter
            if cutoff_date and datetime.fromtimestamp(sub.created) < cutoff_date:
                continue
            
            filtered_subs.append(sub)
        
        # Calculate metrics
        mrr, arr = calculate_mrr_arr(filtered_subs)
        metrics = calculate_churn_metrics(filtered_subs)
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Monthly Recurring Revenue", f"${mrr:,.2f}")
        with col2:
            st.metric("Annual Recurring Revenue", f"${arr:,.2f}")
        with col3:
            st.metric("Active Subscriptions", metrics['active_subscriptions'])
        with col4:
            st.metric("Churn Rate", f"{metrics['churn_rate']:.1f}%")
        
        # Second metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Trialing", metrics['trialing_subscriptions'])
        with col2:
            st.metric("Canceled", metrics['canceled_subscriptions'])
        with col3:
            st.metric("Trial Conversion", f"{metrics['trial_conversion_rate']:.1f}%")
        with col4:
            if len(filtered_subs) != len(all_subscriptions):
                st.metric("Filtered Results", f"{len(filtered_subs)} of {len(all_subscriptions)}")
            else:
                st.metric("Total Subscriptions", len(all_subscriptions))
        
        st.markdown("---")
        
        # Subscription charts
        create_subscription_charts(filtered_subs)
        
        st.markdown("---")
        
        # Subscriptions table
        st.subheader("Subscription Details")
        
        if filtered_subs:
            subs_df = pd.DataFrame([{
                'Customer': sub.customer.name if hasattr(sub.customer, 'name') and sub.customer.name else (sub.customer.email if hasattr(sub.customer, 'email') else f"Customer {sub.customer[-8:] if isinstance(sub.customer, str) else 'Unknown'}"),
                'Status': sub.status.title(),
                'Plan': get_subscription_plan_name(sub),
                'Amount': get_subscription_amount(sub),
                'Interval': get_subscription_interval(sub),
                'Start Date': datetime.fromtimestamp(sub.start_date).strftime('%Y-%m-%d') if hasattr(sub, 'start_date') else 'N/A',
                'Subscription Status': get_subscription_status_info(sub),
                'Subscription ID': sub.id  # Keep for exports but will hide from display
            } for sub in filtered_subs])
            
            # Display table without Subscription ID column (hide from web view)
            display_df = subs_df.drop(columns=['Subscription ID'])
            st.dataframe(display_df, use_container_width=True)
            
            # Populate Quick Actions export buttons with actual data
            with csv_button_placeholder.container():
                # CSV export
                csv_data = subs_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name=f"stripe_subscriptions_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv",
                    key="sub_csv_export"
                )
            
            with excel_button_placeholder.container():
                # Excel export
                from io import BytesIO
                excel_buffer = BytesIO()
                subs_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="📊 Export Excel", 
                    data=excel_data,
                    file_name=f"stripe_subscriptions_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="sub_excel_export"
                )
        else:
            st.info("No subscriptions found matching the selected filters")
    
    else:
        st.info("No subscriptions found")
        with st.expander("💡 Need subscription data?"):
            st.markdown("""
            **Create test subscriptions in Stripe:**
            1. Go to [Stripe Dashboard - Products](https://dashboard.stripe.com/test/products)
            2. Create a product and pricing plan
            3. Create test customers and subscriptions
            4. Use different intervals (monthly, yearly) to see MRR/ARR calculations
            """)

def get_subscription_items_data(subscription):
    """Helper to get subscription items data consistently"""
    
    try:
        # Method 1: Try accessing expanded items data first (modern approach)
        if hasattr(subscription, 'items') and hasattr(subscription.items, 'data'):
            return subscription.items.data
    except:
        pass
    
    try:
        # Method 2: Direct API call for subscription items (most reliable)
        items = stripe.SubscriptionItem.list(subscription=subscription.id)
        if items and items.data:
            return items.data
    except Exception as e:
        pass
    
    try:
        # Method 3: Legacy plan structure (fallback for old subscriptions)
        if hasattr(subscription, 'plan') and subscription.plan:
            # Create a proper item structure for legacy subscriptions
            return [{'price': subscription.plan, 'quantity': getattr(subscription, 'quantity', 1)}]
    except:
        pass
    
    try:
        # Method 4: Try list_subscription_items method
        items_list = subscription.list_subscription_items()
        if items_list and items_list.data:
            return items_list.data
    except:
        pass
    
    return []

def get_subscription_amount(subscription):
    """Get subscription amount as formatted string"""
    items_data = get_subscription_items_data(subscription)
    if items_data and len(items_data) > 0:
        item = items_data[0]
        
        # Get price (handle both objects and dicts)
        price = None
        if hasattr(item, 'price'):  # Real Stripe item object
            price = item.price
        elif isinstance(item, dict) and 'price' in item:  # Our fake dict structure
            price = item['price']
        
        if price:
            # Get quantity (handle both objects and dicts)
            if hasattr(item, 'quantity'):
                quantity = item.quantity
            elif isinstance(item, dict) and 'quantity' in item:
                quantity = item['quantity']
            else:
                quantity = 1
            
            # Get price details - price might be an ID
            if isinstance(price, str):
                try:
                    price = stripe.Price.retrieve(price)
                except:
                    return "$0.00"
            
            # Handle both new Price objects and legacy Plan objects
            if hasattr(price, 'unit_amount') and price.unit_amount:
                amount = (price.unit_amount / 100) * quantity
            elif hasattr(price, 'amount') and price.amount:  # Legacy plan
                amount = (price.amount / 100) * quantity
            else:
                amount = 0
            
            return f"${amount:.2f}"
    return "$0.00"

def get_subscription_interval(subscription):
    """Get subscription billing interval"""
    items_data = get_subscription_items_data(subscription)
    if items_data and len(items_data) > 0:
        item = items_data[0]
        
        # Get price (handle both objects and dicts)
        price = None
        if hasattr(item, 'price'):  # Real Stripe item object
            price = item.price
        elif isinstance(item, dict) and 'price' in item:  # Our fake dict structure
            price = item['price']
        
        if price:
            # Get price details - price might be an ID
            if isinstance(price, str):
                try:
                    price = stripe.Price.retrieve(price)
                except:
                    return 'N/A'
            
            # Handle both new Price objects and legacy Plan objects
            if hasattr(price, 'recurring') and price.recurring:
                return price.recurring.interval
            elif hasattr(price, 'interval'):  # Legacy plan
                return price.interval
    return 'N/A'

def get_subscription_status_info(subscription):
    """Get meaningful subscription status information instead of current period end"""
    
    # Check if subscription is set to cancel
    if hasattr(subscription, 'cancel_at') and subscription.cancel_at:
        cancel_date = datetime.fromtimestamp(subscription.cancel_at).strftime('%Y-%m-%d')
        return f"Cancels {cancel_date}"
    
    # Check if subscription is canceled but still in current period
    if hasattr(subscription, 'canceled_at') and subscription.canceled_at:
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            period_end = datetime.fromtimestamp(subscription.current_period_end).strftime('%Y-%m-%d')
            return f"Canceled, ends {period_end}"
        else:
            return "Canceled"
    
    # Check if subscription is paused
    if hasattr(subscription, 'pause_collection') and subscription.pause_collection:
        if hasattr(subscription.pause_collection, 'resumes_at') and subscription.pause_collection.resumes_at:
            resume_date = datetime.fromtimestamp(subscription.pause_collection.resumes_at).strftime('%Y-%m-%d')
            return f"Paused until {resume_date}"
        else:
            return "Paused indefinitely"
    
    # Check subscription status
    if subscription.status == 'trialing':
        if hasattr(subscription, 'trial_end') and subscription.trial_end:
            trial_end = datetime.fromtimestamp(subscription.trial_end).strftime('%Y-%m-%d')
            return f"Trial ends {trial_end}"
        else:
            return "In trial"
    
    elif subscription.status == 'active':
        # For active subscriptions, show next billing date if available
        if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
            next_billing = datetime.fromtimestamp(subscription.current_period_end).strftime('%Y-%m-%d')
            return f"Next billing {next_billing}"
        else:
            return "Active (ongoing)"
    
    elif subscription.status == 'past_due':
        return "Payment failed"
    
    elif subscription.status == 'incomplete':
        return "Setup incomplete"
    
    elif subscription.status == 'incomplete_expired':
        return "Setup expired"
    
    elif subscription.status == 'unpaid':
        return "Unpaid"
    
    else:
        return subscription.status.title()

def get_subscription_plan_name(subscription):
    """Get a readable plan name from subscription - checks multiple sources"""
    
    # First, check if subscription has a description or metadata
    if hasattr(subscription, 'description') and subscription.description:
        return subscription.description
    
    if hasattr(subscription, 'metadata') and subscription.metadata:
        if 'plan_name' in subscription.metadata:
            return subscription.metadata['plan_name']
        if 'name' in subscription.metadata:
            return subscription.metadata['name']
    
    # Then check subscription items
    items_data = get_subscription_items_data(subscription)
    if items_data and len(items_data) > 0:
        item = items_data[0]
        
        # Check if item has metadata
        if hasattr(item, 'metadata') and item.metadata:
            if 'name' in item.metadata:
                return item.metadata['name']
        
        if hasattr(item, 'price'):
            price = item.price
            
            # Get price details - price might be an ID
            if isinstance(price, str):
                try:
                    price = stripe.Price.retrieve(price)
                except:
                    return "Unknown Plan"
            
            # Try to get product name (will be ID if not expanded)
            if hasattr(price, 'product'):
                if isinstance(price.product, str):
                    # Product is just an ID, try to fetch the name with caching
                    cache_key = f"product_{price.product}"
                    if cache_key in st.session_state:
                        cached_product, timestamp = st.session_state[cache_key]
                        if time.time() - timestamp < 600:  # 10-minute cache
                            if hasattr(cached_product, 'name') and cached_product.name:
                                return cached_product.name
                    
                    try:
                        product = stripe.Product.retrieve(price.product)
                        st.session_state[cache_key] = (product, time.time())
                        if hasattr(product, 'name') and product.name:
                            return product.name
                    except:
                        pass
                elif hasattr(price.product, 'name') and price.product.name:
                    return price.product.name
            
            # Try price metadata
            if hasattr(price, 'metadata') and price.metadata:
                if 'name' in price.metadata:
                    return price.metadata['name']
                if 'plan_name' in price.metadata:
                    return price.metadata['plan_name']
            
            # Fallback to price nickname
            if hasattr(price, 'nickname') and price.nickname:
                return price.nickname
            
            # Fallback to price description
            if hasattr(price, 'lookup_key') and price.lookup_key:
                return price.lookup_key
            
            # Final fallback to amount and interval
            amount = price.unit_amount / 100 if hasattr(price, 'unit_amount') and price.unit_amount else 0
            interval = price.recurring.interval if hasattr(price, 'recurring') and price.recurring else 'one-time'
            return f"${amount:.2f}/{interval}"
    
    return "Unknown Plan"

def create_subscription_charts(subscriptions_data):
    """Create charts for subscription analytics"""
    if not subscriptions_data:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Subscription status breakdown
        status_counts = {}
        for sub in subscriptions_data:
            status = sub.status.title()
            status_counts[status] = status_counts.get(status, 0) + 1
        
        status_df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
        fig_status = px.pie(status_df, values='Count', names='Status', title='Subscriptions by Status')
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Revenue by plan type
        plan_revenue = {}
        for sub in subscriptions_data:
            if sub.status in ['active', 'trialing']:
                plan_name = get_subscription_plan_name(sub)
                amount_str = get_subscription_amount(sub)
                # Extract numeric amount from formatted string like "$10.00"
                try:
                    amount = float(amount_str.replace('$', ''))
                    plan_revenue[plan_name] = plan_revenue.get(plan_name, 0) + amount
                except:
                    pass
        
        if plan_revenue:
            plan_df = pd.DataFrame(list(plan_revenue.items()), columns=['Plan', 'Monthly Revenue'])
            fig_plans = px.bar(plan_df, x='Plan', y='Monthly Revenue', title='Monthly Revenue by Plan')
            fig_plans.update_xaxes(tickangle=45)
            st.plotly_chart(fig_plans, use_container_width=True)

# ============================================================================
# TAGS & NOTES SYSTEM
# ============================================================================

import json
from pathlib import Path

def get_tags_file_path():
    """Get the path to the tags storage file"""
    return Path("data/tags_and_notes.json")

def ensure_data_directory():
    """Ensure the data directory exists"""
    Path("data").mkdir(exist_ok=True)

def load_tags_and_notes():
    """Load tags and notes from JSON file"""
    ensure_data_directory()
    tags_file = get_tags_file_path()
    
    if tags_file.exists():
        try:
            with open(tags_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    return {
        "customer_tags": {},
        "customer_notes": {},
        "transaction_tags": {},
        "transaction_notes": {},
        "tag_definitions": {
            "VIP": {"color": "green", "description": "High-value customer"},
            "Refund Risk": {"color": "red", "description": "Customer with refund history"},
            "New Customer": {"color": "blue", "description": "Recently acquired customer"},
            "Payment Issues": {"color": "orange", "description": "Has payment problems"}
        }
    }

def save_tags_and_notes(data):
    """Save tags and notes to JSON file"""
    ensure_data_directory()
    tags_file = get_tags_file_path()
    
    try:
        with open(tags_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving tags: {str(e)}")
        return False

def add_customer_tag(customer_id, tag):
    """Add a tag to a customer"""
    data = load_tags_and_notes()
    if customer_id not in data["customer_tags"]:
        data["customer_tags"][customer_id] = []
    
    if tag not in data["customer_tags"][customer_id]:
        data["customer_tags"][customer_id].append(tag)
        save_tags_and_notes(data)

def remove_customer_tag(customer_id, tag):
    """Remove a tag from a customer"""
    data = load_tags_and_notes()
    if customer_id in data["customer_tags"] and tag in data["customer_tags"][customer_id]:
        data["customer_tags"][customer_id].remove(tag)
        save_tags_and_notes(data)

def add_customer_note(customer_id, note):
    """Add a note to a customer"""
    data = load_tags_and_notes()
    if customer_id not in data["customer_notes"]:
        data["customer_notes"][customer_id] = []
    
    note_entry = {
        "note": note,
        "timestamp": datetime.now().isoformat(),
        "user": "Dashboard User"
    }
    data["customer_notes"][customer_id].append(note_entry)
    save_tags_and_notes(data)

def get_customer_tags(customer_id):
    """Get all tags for a customer"""
    data = load_tags_and_notes()
    return data["customer_tags"].get(customer_id, [])

def get_customer_notes(customer_id):
    """Get all notes for a customer"""
    data = load_tags_and_notes()
    return data["customer_notes"].get(customer_id, [])

def search_customers_by_tag(tag):
    """Find all customers with a specific tag"""
    data = load_tags_and_notes()
    customers_with_tag = []
    for customer_id, tags in data["customer_tags"].items():
        if tag in tags:
            customers_with_tag.append(customer_id)
    return customers_with_tag

def render_transactions_dashboard():
    """Render the main transactions dashboard (existing functionality)"""
    
    # Auto-detect data range for smart defaults
    if 'data_range_checked' not in st.session_state:
        with st.spinner('Detecting available data range...'):
            oldest_date, newest_date = get_data_date_range()
            
        if oldest_date and newest_date:
            # Set smart defaults based on actual data
            data_span = (newest_date - oldest_date).days
            if data_span <= 30:
                default_start = oldest_date
            elif data_span <= 90:
                default_start = newest_date - timedelta(days=data_span)
            else:
                default_start = newest_date - timedelta(days=90)
            
            st.session_state.smart_start_date = default_start
            st.session_state.smart_end_date = newest_date
            st.session_state.data_span_info = f"Found data from {oldest_date.strftime('%Y-%m-%d')} to {newest_date.strftime('%Y-%m-%d')}"
        else:
            # Fallback to standard defaults
            st.session_state.smart_start_date = datetime.now() - timedelta(days=90)
            st.session_state.smart_end_date = datetime.now()
            st.session_state.data_span_info = "No existing data found"
        
        st.session_state.data_range_checked = True
    
    # Controls moved to tab-specific sections
    # Show data range info at the top if available
    if hasattr(st.session_state, 'data_span_info'):
        st.info(st.session_state.data_span_info)
    
    # Control Panel Header
    st.subheader("📊 Transaction Controls")
    
    # Quick date presets
    st.write("**Quick Date Ranges:**")
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    with preset_col1:
        if st.button("Last 7 Days", key="preset_7d"):
            st.session_state.start_date = datetime.now() - timedelta(days=7)
            st.session_state.end_date = datetime.now()
            st.rerun()
    with preset_col2:
        if st.button("Last 30 Days", key="preset_30d"):
            st.session_state.start_date = datetime.now() - timedelta(days=30)
            st.session_state.end_date = datetime.now()
            st.rerun()
    with preset_col3:
        if st.button("Last 90 Days", key="preset_90d"):
            st.session_state.start_date = datetime.now() - timedelta(days=90)
            st.session_state.end_date = datetime.now()
            st.rerun()
    with preset_col4:
        if st.button("Last Year", key="preset_1y"):
            st.session_state.start_date = datetime.now() - timedelta(days=365)
            st.session_state.end_date = datetime.now()
            st.rerun()
    
    # Date range and filters in organized layout
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.write("**Date Range:**")
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.get('start_date', st.session_state.get('smart_start_date', datetime.now() - timedelta(days=90))).date(),
            key="trans_start_date"
        )
        end_date = st.date_input(
            "End Date", 
            value=st.session_state.get('end_date', st.session_state.get('smart_end_date', datetime.now())).date(),
            key="trans_end_date"
        )
    
    with col2:
        st.write("**Filters:**")
        status_filter = st.multiselect(
            "Payment Status",
            ["succeeded", "failed", "pending", "refunded"],
            default=["succeeded", "pending"],
            key="trans_status_filter"
        )
        
        chart_type = st.selectbox(
            "Chart Type",
            ["Daily Revenue", "Revenue by Product", "Payment Methods", "Both"],
            key="trans_chart_type"
        )
    
    with col3:
        st.write("**Amount Range:**")
        min_amount = st.number_input("Min $", min_value=0.0, value=0.0, step=1.0, key="trans_min_amount")
        max_amount = st.number_input("Max $", min_value=0.0, value=10000.0, step=1.0, key="trans_max_amount")
    
    st.markdown("---")
    
    # Convert to datetime for API
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Fetch data
    with st.spinner('Fetching Stripe data...'):
        raw_charges_data = get_stripe_data(start_datetime, end_datetime)
        charges_data = filter_charges_data(raw_charges_data, status_filter, min_amount, max_amount)
    
    # Show filtering info
    if raw_charges_data and len(charges_data) != len(raw_charges_data):
        st.info(f"Showing {len(charges_data)} of {len(raw_charges_data)} transactions (filtered)")
    
    if charges_data:
        # Main metrics
        total_revenue = sum(charge.amount for charge in charges_data) / 100
        total_transactions = len(charges_data)
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        with col2:
            st.metric("Total Transactions", total_transactions)
        with col3:
            st.metric("Avg Transaction", f"${avg_transaction:.2f}")
        
        st.markdown("---")
        
        # Display charts based on selection
        if chart_type == "Daily Revenue":
            fig = create_revenue_chart(charges_data)
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Revenue by Product":
            fig = create_product_chart(charges_data)
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Payment Methods":
            fig = create_payment_method_chart(charges_data)
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Both":
            col1, col2 = st.columns(2)
            with col1:
                fig_revenue = create_revenue_chart(charges_data)
                st.plotly_chart(fig_revenue, use_container_width=True)
            with col2:
                fig_product = create_product_chart(charges_data)
                st.plotly_chart(fig_product, use_container_width=True)
        
        # Transaction details
        st.subheader("Transactions")
        
        def get_customer_name(charge):
            if not charge.customer:
                return 'Guest'
            
            # If customer is expanded, get the name
            if hasattr(charge.customer, 'name') and charge.customer.name:
                return charge.customer.name
            elif hasattr(charge.customer, 'email') and charge.customer.email:
                return charge.customer.email
            elif isinstance(charge.customer, str):
                # Customer ID not expanded, show truncated ID
                return f"Customer {charge.customer[-8:]}"
            else:
                return 'Guest'
        
        def get_product_info(charge):
            # Try to get from metadata first (most reliable for custom implementations)
            if hasattr(charge, 'metadata') and charge.metadata:
                if 'product_name' in charge.metadata:
                    return charge.metadata['product_name']
                elif 'product' in charge.metadata:
                    return charge.metadata['product']
                elif 'item_name' in charge.metadata:
                    return charge.metadata['item_name']
            
            # Try to get from description
            if hasattr(charge, 'description') and charge.description:
                # Clean up common payment processor descriptions
                desc = charge.description
                if not desc.lower().startswith('payment for'):
                    return desc
            
            # Try to get from receipt_email or statement_descriptor
            if hasattr(charge, 'statement_descriptor') and charge.statement_descriptor:
                return charge.statement_descriptor
            
            # Default fallback
            return 'Payment'
        
        df = pd.DataFrame([{
            'Date': datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M'),
            'Amount': f"${charge.amount / 100:.2f}",
            'Product': get_product_info(charge),
            'Currency': charge.currency.upper(),
            'Status': charge.status.title(),
            'Customer': get_customer_name(charge)
        } for charge in charges_data])
        
        st.dataframe(df, use_container_width=True)
        
        # Export functionality
        st.subheader("Export Data")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV export
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"stripe_transactions_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Filtered summary CSV
            summary_data = pd.DataFrame([{
                'Date Range': f"{start_date} to {end_date}",
                'Total Transactions': total_transactions,
                'Total Revenue': f"${total_revenue:,.2f}",
                'Average Transaction': f"${avg_transaction:.2f}",
                'Filters Applied': f"Status: {', '.join(status_filter)}, Amount: ${min_amount}-${max_amount}"
            }])
            summary_csv = summary_data.to_csv(index=False)
            st.download_button(
                label="📊 Download Summary",
                data=summary_csv,
                file_name=f"stripe_summary_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        
        with col3:
            # Export all data (not just displayed 10 rows)
            all_transactions_df = pd.DataFrame([{
                'Date': datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M'),
                'Amount': f"${charge.amount / 100:.2f}",
                'Product': get_product_info_for_chart(charge),
                'Currency': charge.currency.upper(),
                'Status': charge.status.title(),
                'Customer': get_customer_name_for_export(charge),
                'Payment Method': get_detailed_payment_method(charge),
                'Charge ID': charge.id
            } for charge in charges_data])
            
            all_csv = all_transactions_df.to_csv(index=False)
            st.download_button(
                label="📋 Download All Data",
                data=all_csv,
                file_name=f"stripe_all_transactions_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        
    else:
        st.info("No transactions found for the selected date range")
        st.markdown("""
        **Try expanding your date range:**
        - Use the quick preset buttons in the sidebar (Last Year is often helpful)
        - Or manually adjust the Custom Date Range
        - Make sure your Stripe account has test transactions in the selected period
        """)
        
        # Show suggestion to create test data
        with st.expander("💡 Need test data?"):
            st.markdown("""
            **Create test transactions in Stripe:**
            1. Go to [Stripe Dashboard - Test Mode](https://dashboard.stripe.com/test/payments)
            2. Use test card: `4242424242424242`
            3. Any future expiry date and any 3-digit CVC
            4. Create a few test payments to see your dashboard in action!
            """)

def main():
    st.title("💳 Stripe Dashboard")
    
    # Check if Stripe is configured first
    if not os.getenv('STRIPE_SECRET_KEY'):
        st.error("⚠️ Stripe API key not configured. Please set STRIPE_SECRET_KEY in your .env file")
        st.info("Copy .env.example to .env and add your Stripe API keys")
        return
    
    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["📊 Transactions", "👥 Customers", "🔄 Subscriptions"])
    
    with tab1:
        render_transactions_dashboard()
    
    with tab2:
        render_customers_dashboard()
    
    with tab3:
        render_subscriptions_dashboard()

if __name__ == "__main__":
    main()
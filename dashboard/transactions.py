import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from services.stripe_service import get_stripe_data, filter_charges_data, get_data_date_range
from analytics.charts import create_revenue_chart, create_product_chart, create_payment_method_chart
from utils.formatters import get_product_info_for_chart, get_customer_name_for_export

def render_transactions_dashboard():
    """Render the main transactions dashboard"""
    
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
            
            st.session_state['smart_start_date'] = default_start
            st.session_state['smart_end_date'] = newest_date
            st.session_state['data_span_info'] = f"Found data from {oldest_date.strftime('%Y-%m-%d')} to {newest_date.strftime('%Y-%m-%d')}"
        else:
            # Fallback to standard defaults
            st.session_state['smart_start_date'] = datetime.now() - timedelta(days=90)
            st.session_state['smart_end_date'] = datetime.now()
            st.session_state['data_span_info'] = "No existing data found"
        
        st.session_state['data_range_checked'] = True
    
    # Show data range info at the top if available
    if 'data_span_info' in st.session_state:
        st.info(st.session_state['data_span_info'])
    
    # Control Panel Header
    st.subheader("📊 Transaction Controls")
    
    # Quick date presets
    st.write("**Quick Date Ranges:**")
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    with preset_col1:
        if st.button("Last 7 Days", key="preset_7d"):
            st.session_state['start_date'] = datetime.now() - timedelta(days=7)
            st.session_state['end_date'] = datetime.now()
            st.rerun()
    with preset_col2:
        if st.button("Last 30 Days", key="preset_30d"):
            st.session_state['start_date'] = datetime.now() - timedelta(days=30)
            st.session_state['end_date'] = datetime.now()
            st.rerun()
    with preset_col3:
        if st.button("Last 90 Days", key="preset_90d"):
            st.session_state['start_date'] = datetime.now() - timedelta(days=90)
            st.session_state['end_date'] = datetime.now()
            st.rerun()
    with preset_col4:
        if st.button("Last Year", key="preset_1y"):
            st.session_state['start_date'] = datetime.now() - timedelta(days=365)
            st.session_state['end_date'] = datetime.now()
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
        st.write("**Show only:**")
        filter_option = st.selectbox(
            "Transaction Type",
            options=["All Transactions", "Succeeded Only", "Other Only"],
            index=0,
            key="trans_filter_option",
            help="Choose which transactions to display"
        )
        
        # Convert dropdown selection to status list
        # All possible Stripe charge statuses based on web interface URLs
        ALL_STATUSES = [
            # Basic statuses
            "succeeded", "failed", "pending", "canceled",
            # Refund statuses  
            "refunded", "refund_pending", "partially_refunded",
            # Dispute statuses
            "disputed", "lost", "won", "dispute_under_review", 
            "dispute_needs_response", "closed", 
            "inquiry_under_review", "inquiry_needs_response"
        ]
        
        if filter_option == "All Transactions":
            status_filter = ALL_STATUSES
        elif filter_option == "Succeeded Only":
            status_filter = ["succeeded"]
        else:  # "Other Only"
            status_filter = [s for s in ALL_STATUSES if s != "succeeded"]
        
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
    
    # Convert dates to datetime objects
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Fetch and process data
    with st.spinner('Loading transaction data...'):
        charges_data = get_stripe_data(start_datetime, end_datetime)
        
        if not charges_data:
            st.warning("No transaction data found for the selected date range.")
            return
        
        # Apply filters
        filtered_data = filter_charges_data(charges_data, status_filter, min_amount, max_amount)
        
            
        if not filtered_data:
            st.warning("No transactions match the selected filters.")
            return
    
    # Show current filter summary
    st.success(f"📊 Showing {len(filtered_data)} transactions ({filter_option}) from {len(charges_data)} total")
    
    # Display metrics
    total_revenue = sum(charge.amount / 100 for charge in filtered_data if charge.status == 'succeeded')
    total_transactions = len(filtered_data)
    avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    with metric_col2:
        st.metric("Total Transactions", total_transactions)
    with metric_col3:
        st.metric("Average Transaction", f"${avg_transaction:.2f}")
    
    # Display charts
    if chart_type == "Daily Revenue":
        fig_revenue = create_revenue_chart(filtered_data)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    elif chart_type == "Both":
        col1, col2 = st.columns(2)
        with col1:
            fig_revenue = create_revenue_chart(filtered_data)
            st.plotly_chart(fig_revenue, use_container_width=True)
        with col2:
            fig_product = create_product_chart(filtered_data)
            st.plotly_chart(fig_product, use_container_width=True)
    
    elif chart_type == "Revenue by Product":
        fig_product = create_product_chart(filtered_data)
        st.plotly_chart(fig_product, use_container_width=True)
    
    elif chart_type == "Payment Methods":
        fig_payment = create_payment_method_chart(filtered_data)
        st.plotly_chart(fig_payment, use_container_width=True)
    
    # Transaction details
    st.subheader("Transactions")
    
    def get_customer_name(charge):
        if not charge.customer:
            return 'Guest'
        
        # If customer is expanded, get the name or email
        if hasattr(charge.customer, 'name') and charge.customer.name:
            return charge.customer.name
        elif hasattr(charge.customer, 'email') and charge.customer.email:
            return charge.customer.email
        elif isinstance(charge.customer, str):
            return charge.customer[-8:]  # Show last 8 chars of ID
        else:
            return 'Guest'
    
    def get_product_info(charge):
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
    } for charge in filtered_data])
    
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
        # Excel export
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_data = excel_buffer.getvalue()
        st.download_button(
            label="📊 Download Excel", 
            data=excel_data,
            file_name=f"stripe_transactions_{start_date}_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
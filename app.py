import streamlit as st
import stripe
from datetime import datetime, timedelta

# Import configuration
from config.settings import STRIPE_SECRET_KEY

# Import services
from services.cache_service import clear_stripe_cache
from services.stripe_service import get_customers_data, get_all_subscriptions

# Import dashboard components
from dashboard.transactions import render_transactions_dashboard

# Import remaining functionality from original file for now
# (These will be extracted in subsequent iterations)
from app_original import (
    render_customers_dashboard,
    render_subscriptions_dashboard
)

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

def check_authentication():
    """Handle authentication logic"""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # If not authenticated, show login form
    if not st.session_state.authenticated:
        st.title("🏊‍♂️ Team Orlando Water Polo Club")
        st.subheader("Dashboard Access")
        
        with st.form("login_form"):
            st.write("Please enter your credentials to access the dashboard:")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                # Get credentials from secrets or environment with proper fallback
                try:
                    valid_username = st.secrets.get("DASHBOARD_USERNAME")
                    valid_password = st.secrets.get("DASHBOARD_PASSWORD")
                    if not valid_username or not valid_password:
                        st.error("❌ Authentication credentials not configured. Please set DASHBOARD_USERNAME and DASHBOARD_PASSWORD in Streamlit secrets.")
                        st.stop()
                except (AttributeError, FileNotFoundError):
                    st.error("❌ Authentication system requires secrets configuration. Please configure DASHBOARD_USERNAME and DASHBOARD_PASSWORD.")
                    st.info("💡 For local development, create `.streamlit/secrets.toml` with your credentials.")
                    st.stop()
                
                if username == valid_username and password == valid_password:
                    st.session_state.authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.stop()

def main():
    """Main application function"""
    st.set_page_config(
        page_title="Team Orlando Water Polo Club - Stripe Dashboard",
        page_icon="🏊‍♂️",
        layout="wide"
    )
    
    # Check authentication first
    check_authentication()
    
    # App header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🏊‍♂️ Team Orlando Water Polo Club")
        st.subheader("Stripe Financial Dashboard")
    with col2:
        st.write("")  # Add some spacing
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs([
        "💳 Transactions", 
        "👥 Customers", 
        "🔄 Subscriptions"
    ])
    
    with tab1:
        render_transactions_dashboard()
    
    with tab2:
        render_customers_dashboard()
    
    with tab3:
        render_subscriptions_dashboard()
    
    # Cache management in sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        if st.button("🔄 Clear Cache"):
            clear_stripe_cache()
            st.success("Cache cleared!")
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Dashboard Status**")
        st.success("✅ Connected to Stripe")
        
        # Show some basic stats
        try:
            customers_count = len(get_customers_data())
            subscriptions_count = len(get_all_subscriptions())
            
            st.info(f"👥 {customers_count} customers")
            st.info(f"🔄 {subscriptions_count} subscriptions")
            
        except Exception as e:
            st.error("Unable to load basic stats")

if __name__ == "__main__":
    main()
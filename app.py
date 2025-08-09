import streamlit as st
import stripe
from datetime import datetime, timedelta

# Import configuration
from config.settings import STRIPE_SECRET_KEY

# Import services
from services.cache_service import clear_stripe_cache
from services.stripe_service import get_customers_data, get_all_subscriptions
from services.ai_service import generate_claude_recommendations

# Import models
from models.customer_data import load_tags_and_notes

# Import analytics
from analytics.calculations import calculate_mrr_arr, calculate_churn_metrics
from analytics.fees import calculate_stripe_fees

# Import dashboard components
from dashboard.transactions import render_transactions_dashboard

# Import remaining functionality from original file for now
# (These will be extracted in subsequent iterations)
from app_original import (
    render_customers_dashboard,
    render_subscriptions_dashboard, 
    render_reports_section,
    render_analytics_insights
)

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

def main():
    """Main application function"""
    st.set_page_config(
        page_title="Team Orlando Water Polo Club - Stripe Dashboard",
        page_icon="🏊‍♂️",
        layout="wide"
    )
    
    # App header
    st.title("🏊‍♂️ Team Orlando Water Polo Club")
    st.subheader("Stripe Financial Dashboard")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💳 Transactions", 
        "👥 Customers", 
        "🔄 Subscriptions", 
        "📋 Reports", 
        "🤖 Analytics & AI Insights"
    ])
    
    with tab1:
        render_transactions_dashboard()
    
    with tab2:
        render_customers_dashboard()
    
    with tab3:
        render_subscriptions_dashboard()
    
    with tab4:
        render_reports_section()
    
    with tab5:
        render_analytics_insights()
    
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
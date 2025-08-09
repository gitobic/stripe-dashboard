import streamlit as st
import time
from functools import wraps
from config.settings import CACHE_TTL_SECONDS

def cache_stripe_data(ttl_seconds=CACHE_TTL_SECONDS):
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
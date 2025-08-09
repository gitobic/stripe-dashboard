import os
from dotenv import load_dotenv

try:
    import streamlit as st
    # Running in Streamlit environment
    def get_secret(key, default=None):
        """Get secret from Streamlit secrets or environment variables"""
        try:
            # Try Streamlit secrets first (for cloud deployment)
            return st.secrets.get(key, os.getenv(key, default))
        except (AttributeError, FileNotFoundError):
            # Fallback to environment variables (for local development)
            return os.getenv(key, default)
except ImportError:
    # Not running in Streamlit environment, use standard env vars
    def get_secret(key, default=None):
        return os.getenv(key, default)

# Load environment variables for local development
load_dotenv()

# Get API keys with fallback logic
STRIPE_SECRET_KEY = get_secret('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = get_secret('STRIPE_PUBLISHABLE_KEY')

CACHE_TTL_SECONDS = 300  # 5-minute cache
CUSTOMER_CACHE_TTL_SECONDS = 600  # 10-minute cache for customers/subscriptions

DATA_DIR = "data"
TAGS_FILE = "data/tags_and_notes.json"
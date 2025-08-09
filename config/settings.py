import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

CACHE_TTL_SECONDS = 300  # 5-minute cache
CUSTOMER_CACHE_TTL_SECONDS = 600  # 10-minute cache for customers/subscriptions

DATA_DIR = "data"
TAGS_FILE = "data/tags_and_notes.json"
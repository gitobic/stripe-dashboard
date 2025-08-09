"""Mock Stripe objects for testing"""
from datetime import datetime
from typing import Dict, Any

class MockStripeCharge:
    """Mock Stripe Charge object"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'ch_test123')
        self.amount = kwargs.get('amount', 2500)  # $25.00 in cents
        self.currency = kwargs.get('currency', 'usd')
        self.status = kwargs.get('status', 'succeeded')
        self.created = kwargs.get('created', int(datetime.now().timestamp()))
        self.description = kwargs.get('description', 'Test payment')
        self.customer = kwargs.get('customer', 'cus_test123')
        self.metadata = kwargs.get('metadata', {})
        self.payment_method_details = kwargs.get('payment_method_details', None)
        self.source = kwargs.get('source', None)
        self.statement_descriptor = kwargs.get('statement_descriptor', None)

class MockStripeCustomer:
    """Mock Stripe Customer object"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'cus_test123')
        self.name = kwargs.get('name', 'John Doe')
        self.email = kwargs.get('email', 'john@example.com')
        self.created = kwargs.get('created', int(datetime.now().timestamp()))
        self.description = kwargs.get('description', 'Test customer')

class MockStripeSubscription:
    """Mock Stripe Subscription object"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'sub_test123')
        self.status = kwargs.get('status', 'active')
        self.customer = kwargs.get('customer', 'cus_test123')
        self.created = kwargs.get('created', int(datetime.now().timestamp()))
        self.items = kwargs.get('items', MockStripeSubscriptionItems())
        
class MockStripeSubscriptionItems:
    """Mock Stripe Subscription Items"""
    def __init__(self, **kwargs):
        self.data = kwargs.get('data', [MockStripeSubscriptionItem()])

class MockStripeSubscriptionItem:
    """Mock Stripe Subscription Item"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'si_test123')
        self.price = kwargs.get('price', MockStripePrice())
        self.quantity = kwargs.get('quantity', 1)

class MockStripePrice:
    """Mock Stripe Price object"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'price_test123')
        self.unit_amount = kwargs.get('unit_amount', 2000)  # $20.00
        self.currency = kwargs.get('currency', 'usd')
        self.recurring = kwargs.get('recurring', MockStripeRecurring())
        self.product = kwargs.get('product', MockStripeProduct())

class MockStripeRecurring:
    """Mock Stripe Recurring object"""
    def __init__(self, **kwargs):
        self.interval = kwargs.get('interval', 'month')
        self.interval_count = kwargs.get('interval_count', 1)

class MockStripeProduct:
    """Mock Stripe Product object"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'prod_test123')
        self.name = kwargs.get('name', 'Test Product')
        self.description = kwargs.get('description', 'Test product description')

class MockPaymentMethodDetails:
    """Mock Stripe Payment Method Details"""
    def __init__(self, **kwargs):
        self.type = kwargs.get('type', 'card')
        self.card = kwargs.get('card', MockCard())

class MockCard:
    """Mock Stripe Card object"""
    def __init__(self, **kwargs):
        self.brand = kwargs.get('brand', 'visa')
        self.wallet = kwargs.get('wallet', None)

def create_mock_charges(count: int = 5) -> list:
    """Create multiple mock charges for testing"""
    charges = []
    for i in range(count):
        charge = MockStripeCharge(
            id=f'ch_test{i+1}',
            amount=(i+1) * 1000,  # $10, $20, $30, etc.
            status='succeeded' if i % 2 == 0 else 'failed',
            created=int(datetime.now().timestamp()) - (i * 86400),  # Different days
            customer=f'cus_test{i+1}',
            description=f'Test payment {i+1}'
        )
        charges.append(charge)
    return charges

def create_mock_customers(count: int = 3) -> list:
    """Create multiple mock customers for testing"""
    customers = []
    for i in range(count):
        customer = MockStripeCustomer(
            id=f'cus_test{i+1}',
            name=f'Customer {i+1}',
            email=f'customer{i+1}@example.com'
        )
        customers.append(customer)
    return customers

def create_mock_subscriptions(count: int = 3) -> list:
    """Create multiple mock subscriptions for testing"""
    subscriptions = []
    statuses = ['active', 'trialing', 'canceled']
    for i in range(count):
        subscription = MockStripeSubscription(
            id=f'sub_test{i+1}',
            status=statuses[i % len(statuses)],
            customer=f'cus_test{i+1}'
        )
        subscriptions.append(subscription)
    return subscriptions
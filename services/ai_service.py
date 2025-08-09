from anthropic import Anthropic
from config.settings import ANTHROPIC_API_KEY

def setup_claude():
    """Setup Claude AI client"""
    try:
        if not ANTHROPIC_API_KEY:
            return None, "Anthropic API key not configured in .env file"
        
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        return client, None
    except Exception as e:
        return None, f"Error setting up Claude: {str(e)}"

def generate_claude_summary(data_summary, period_info):
    """Generate a Claude-powered summary report"""
    client, error = setup_claude()
    if error:
        return f"Claude summary not available: {error}"
    
    try:
        prompt = f"""
        Create a concise, plain-English business summary for Team Orlando Water Polo Club based on this financial data:

        PERIOD: {period_info}
        
        DATA SUMMARY:
        {data_summary}
        
        Please provide:
        1. A 2-3 sentence executive summary
        2. Key highlights (positive trends, concerns)
        3. Simple recommendations for the board
        
        Keep it conversational and actionable for a non-technical board of directors.
        """
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{
                "role": "user", 
                "content": prompt
            }]
        )
        
        return response.content[0].text
    except Exception as e:
        return f"Error generating Claude summary: {str(e)}"

def generate_claude_recommendations(fee_analysis, customer_data, subscription_data, period_info):
    """Generate Claude-powered business recommendations"""
    client, error = setup_claude()
    if error:
        return f"AI recommendations not available: {error}"
    
    try:
        prompt = f"""
        As a business consultant for Team Orlando Water Polo Club, analyze this data and provide strategic recommendations:

        ANALYSIS PERIOD: {period_info}
        
        STRIPE FEE ANALYSIS:
        {fee_analysis}
        
        CUSTOMER INSIGHTS:
        - Total customers: {len(customer_data) if customer_data else 0}
        - Customer engagement patterns based on transaction frequency
        
        SUBSCRIPTION METRICS:
        - Active subscriptions providing recurring revenue
        - Member retention and churn patterns
        
        Please provide:
        1. COST OPTIMIZATION: Specific ways to reduce Stripe processing fees
        2. REVENUE GROWTH: Actionable strategies to increase revenue
        3. CUSTOMER RETENTION: Methods to improve member engagement and reduce churn
        4. OPERATIONAL EFFICIENCY: Process improvements for the finance team
        
        Keep recommendations practical and specific to a sports club's needs.
        Prioritize high-impact, easy-to-implement suggestions first.
        """
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=800,
            messages=[{
                "role": "user", 
                "content": prompt
            }]
        )
        
        return response.content[0].text
    except Exception as e:
        return f"Error generating AI recommendations: {str(e)}"
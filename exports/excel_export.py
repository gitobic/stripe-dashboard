import pandas as pd
from io import BytesIO
from datetime import datetime
import openpyxl

def create_excel_report(transactions_df, customers_df, subscriptions_df, summary_text):
    """Create a comprehensive Excel report with multiple sheets"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write each dataframe to a different sheet
        if not transactions_df.empty:
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
        
        if not customers_df.empty:
            customers_df.to_excel(writer, sheet_name='Customers', index=False)
        
        if not subscriptions_df.empty:
            subscriptions_df.to_excel(writer, sheet_name='Subscriptions', index=False)
        
        # Create a summary sheet
        summary_df = pd.DataFrame({
            'Report Section': ['Executive Summary', 'Generated On'],
            'Content': [summary_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    return output.getvalue()
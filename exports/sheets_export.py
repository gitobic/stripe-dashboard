import gspread
import json
from google.oauth2.service_account import Credentials
from config.settings import GOOGLE_SERVICE_ACCOUNT_JSON

def setup_google_sheets():
    """Setup Google Sheets API connection"""
    try:
        # Check if Google service account credentials are configured
        if not GOOGLE_SERVICE_ACCOUNT_JSON:
            return None, "Google Service Account JSON not configured in .env file"
        
        # Parse the credentials JSON
        creds_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 
                   'https://www.googleapis.com/auth/drive']
        )
        
        gc = gspread.authorize(credentials)
        return gc, None
    except Exception as e:
        return None, f"Error setting up Google Sheets: {str(e)}"

def export_to_google_sheets(df, sheet_name, worksheet_title="Sheet1"):
    """Export DataFrame to Google Sheets"""
    gc, error = setup_google_sheets()
    if error:
        return False, error
    
    try:
        # Try to open existing sheet or create new one
        try:
            sheet = gc.open(sheet_name)
        except gspread.SpreadsheetNotFound:
            sheet = gc.create(sheet_name)
            # Make sheet accessible to anyone with link (optional)
            sheet.share('', perm_type='anyone', role='reader')
        
        # Get or create worksheet
        try:
            worksheet = sheet.worksheet(worksheet_title)
            worksheet.clear()  # Clear existing data
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=worksheet_title, rows=len(df)+10, cols=len(df.columns)+5)
        
        # Convert DataFrame to list of lists for gspread
        data = [df.columns.tolist()] + df.values.tolist()
        worksheet.update('A1', data)
        
        return True, f"Data exported to Google Sheets: {sheet.url}"
    except Exception as e:
        return False, f"Error exporting to Google Sheets: {str(e)}"
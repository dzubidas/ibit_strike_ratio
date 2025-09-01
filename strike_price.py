import requests
import os
import sys
import time
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not available, using system environment variables")

# Google Sheets integration
SHEETS_AVAILABLE = False

def import_sheets_modules():
    """Safely import Google Sheets modules"""
    global SHEETS_AVAILABLE
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        SHEETS_AVAILABLE = True
        print("✅ Google Sheets integration available")
        return gspread, Credentials
    except ImportError as e:
        print(f"⚠️  Google Sheets libraries not available: {e}")
        SHEETS_AVAILABLE = False
        return None, None

# Configuration
class Config:
    CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'service-account-key.json')
    SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    WORKSHEET_ID = int(os.getenv('GOOGLE_WORKSHEET_ID', 0))
    
    # Fixed BlackRock ratio (Aug 29, 2025: 746,810.57340 BTC ÷ 1,314,880,000 shares)
    BTC_PER_IBIT_RATIO = 746810.57340 / 1314880000
    
    # ETHA Configuration
    ETHA_UNITS = float(os.getenv('ETHA_UNITS', 3777263.17140))
    ETHA_SHARES_OUTSTANDING = float(os.getenv('ETHA_SHARES_OUTSTANDING', 499320000))
    ETHA_RATIO = ETHA_UNITS / ETHA_SHARES_OUTSTANDING
    GOOGLE_WORKSHEET_ID_2 = int(os.getenv('GOOGLE_WORKSHEET_ID_2', 1))
    
class SheetsManager:
    """Google Sheets connection and data management"""
    
    def __init__(self):
        self.gc = None
        self.sheet = None
        self.worksheet = None
        self.gspread = None
        self.Credentials = None
        
    def setup_sheets(self, worksheet_id=None):
        """Initialize Google Sheets connection"""
        self.gspread, self.Credentials = import_sheets_modules()
        
        if not SHEETS_AVAILABLE or not Config.SHEET_ID:
            return False
            
        if not os.path.exists(Config.CREDENTIALS_FILE):
            print(f"❌ Credentials file not found: {Config.CREDENTIALS_FILE}")
            return False
            
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = self.Credentials.from_service_account_file(Config.CREDENTIALS_FILE, scopes=scope)
            self.gc = self.gspread.authorize(creds)
            self.sheet = self.gc.open_by_key(Config.SHEET_ID)
            # Use provided worksheet_id or default
            target_worksheet_id = worksheet_id if worksheet_id is not None else Config.WORKSHEET_ID
            self.worksheet = self.sheet.get_worksheet_by_id(target_worksheet_id)
            print("✅ Connected to Google Sheets")
            return True
        except Exception as e:
            print(f"❌ Sheets connection failed: {e}")
            return False
    
    def set_worksheet(self, worksheet_id):
        """Set the active worksheet"""
        try:
            if self.sheet:
                self.worksheet = self.sheet.get_worksheet_by_id(worksheet_id)
                return True
            return False
        except Exception as e:
            print(f"❌ Error setting worksheet {worksheet_id}: {e}")
            return False
    
    def upload_to_sheets(self, table_data, current_price, etf_type="IBIT"):
        """Upload strike table data to Google Sheets"""
        if not self.worksheet:
            return False
            
        try:
            self.worksheet.clear()
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if etf_type == "IBIT":
                header_data = [
                    ['IBIT Strike to BTC Price Calculator'],
                    [''],
                    [f'Updated: {timestamp}'],
                    [f'Current IBIT Price: ${current_price:,.2f}'],
                    [f'Shares Outstanding: 1,314,880,000'],
                    [f'IBIT BTC units: 746,810.57340'],
                    [f'Formula: BTC = IBIT ÷ {Config.BTC_PER_IBIT_RATIO}'],
                    [f'BlackRock Official Ratio: {Config.BTC_PER_IBIT_RATIO}'],
                    [''],
                    ['IBIT Strike Price', 'BTC Equivalent Price']
                ]
            else:  # ETHA
                header_data = [
                    ['ETHA Strike to BTC Price Calculator'],
                    [''],
                    [f'Updated: {timestamp}'],
                    [f'Current ETHA Price: ${current_price:,.2f}'],
                    [f'Shares Outstanding: {Config.ETHA_SHARES_OUTSTANDING:,.0f}'],
                    [f'ETHA ETH units: {Config.ETHA_UNITS:,.5f}'],
                    [f'Formula: BTC = ETHA ÷ {Config.ETHA_RATIO:.10f}'],
                    [f'ETHA Official Ratio: {Config.ETHA_RATIO:.10f}'],
                    [''],
                    ['ETHA Strike Price', 'BTC Equivalent Price']
                ]
            
            table_rows = []
            for row in table_data:
                table_rows.append([
                    f'${row["strike"]:.2f}',
                    f'${row["btc_equivalent"]:,.2f}'
                ])
            
            all_data = header_data + table_rows
            self.worksheet.update('A1', all_data, value_input_option='USER_ENTERED')
            print(f"✅ {etf_type} data uploaded to Google Sheets")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading {etf_type} to Google Sheets: {e}")
            return False

def get_ibit_price():
    """Get current IBIT price from Yahoo Finance"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/IBIT"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Ubuntu) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        ibit_price = data['chart']['result'][0]['meta']['regularMarketPrice']
        print(f"📈 IBIT Price: ${ibit_price:,.2f}")
        return ibit_price
        
    except Exception as e:
        print(f"❌ Error getting IBIT price: {e}")
        return None

def get_etha_price():
    """Get current ETHA price from Yahoo Finance"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/ETHA"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Ubuntu) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        etha_price = data['chart']['result'][0]['meta']['regularMarketPrice']
        print(f"📈 ETHA Price: ${etha_price:,.2f}")
        return etha_price
        
    except Exception as e:
        print(f"❌ Error getting ETHA price: {e}")
        return None

def calculate_strike_table(strike_range=(25, 80)):
    """Calculate BTC equivalent for each IBIT strike using fixed formula"""
    table_data = []
    
    # Generate strikes in 0.5 increments
    strike = strike_range[0]
    while strike <= strike_range[1]:
        # Formula: Bitcoin Price = IBIT Price ÷ 0.000568058
        btc_equivalent = strike / Config.BTC_PER_IBIT_RATIO
        
        table_data.append({
            'strike': strike,
            'btc_equivalent': btc_equivalent
        })
        
        strike += 0.5  # Increment by 0.5
    
    print(f"📊 Generated {len(table_data)} strike levels using formula: BTC = IBIT ÷ {Config.BTC_PER_IBIT_RATIO}")
    return table_data

def calculate_etha_strike_table(strike_range=(25, 80)):
    """Calculate BTC equivalent for each ETHA strike using ETHA ratio"""
    table_data = []
    
    # Generate strikes in 0.5 increments
    strike = strike_range[0]
    while strike <= strike_range[1]:
        # Formula: BTC Equivalent = ETHA Price / ETHA_RATIO
        btc_equivalent = strike / Config.ETHA_RATIO
        
        table_data.append({
            'strike': strike,
            'btc_equivalent': btc_equivalent
        })
        
        strike += 0.5  # Increment by 0.5
    
    print(f"📊 Generated {len(table_data)} ETHA strike levels using ratio: {Config.ETHA_RATIO:.10f}")
    return table_data

def print_table(table_data, current_price, etf_type="IBIT"):
    """Print formatted table to terminal"""
    if etf_type == "IBIT":
        current_btc_equivalent = current_price / Config.BTC_PER_IBIT_RATIO
        ratio = Config.BTC_PER_IBIT_RATIO
        title = "IBIT STRIKE TO BTC PRICE CALCULATOR"
        strike_label = "IBIT Strike"
    else:  # ETHA
        current_btc_equivalent = current_price / Config.ETHA_RATIO
        ratio = Config.ETHA_RATIO
        title = "ETHA STRIKE TO BTC PRICE CALCULATOR"
        strike_label = "ETHA Strike"
    
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(f"Current {etf_type} Price: ${current_price:,.2f}")
    print(f"Current BTC Equivalent: ${current_btc_equivalent:,.2f}")
    print(f"Formula: BTC = {etf_type} ÷ {ratio:.10f}")
    print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print(f"{strike_label:<15} | {'BTC Equivalent':<15}")
    print("-" * 80)
    
    for row in table_data:
        strike = row['strike']
        btc_equivalent = row['btc_equivalent']
        
        # Highlight current level
        highlight = " 🎯" if abs(strike - current_price) < 2 else ""
        
        print(f"${strike:<14.2f} | ${btc_equivalent:<14,.2f}{highlight}")
    
    print("=" * 80)
    print(f"🎯 = Near current {etf_type} price")

def main():
    """Main function"""
    print("🚀 Starting IBIT & ETHA Strike Calculator...")
    print(f"🔢 Using formulas:")
    print(f"   IBIT: Bitcoin Price = IBIT Price ÷ {Config.BTC_PER_IBIT_RATIO}")
    print(f"   ETHA: Bitcoin Price = ETHA Price ÷ {Config.ETHA_RATIO:.10f}")
    
    # Get IBIT price
    ibit_price = get_ibit_price()
    if not ibit_price:
        print("❌ Failed to fetch IBIT price")
        return 1
    
    # Get ETHA price
    etha_price = get_etha_price()
    if not etha_price:
        print("❌ Failed to fetch ETHA price")
        return 1
    
    # Calculate strike tables
    ibit_table_data = calculate_strike_table()
    etha_table_data = calculate_etha_strike_table((10, 70))
    
    # Print results
    print_table(ibit_table_data, ibit_price, "IBIT")
    print_table(etha_table_data, etha_price, "ETHA")
    
    # Update Google Sheets for IBIT
    print("\n📊 Attempting to update IBIT Google Sheets...")
    ibit_sheets_manager = SheetsManager()
    
    if ibit_sheets_manager.setup_sheets(Config.WORKSHEET_ID):
        if ibit_sheets_manager.upload_to_sheets(ibit_table_data, ibit_price, "IBIT"):
            print("✅ IBIT Google Sheets updated successfully")
        else:
            print("⚠️  IBIT Google Sheets update failed")
    else:
        print("⚠️  Continuing without IBIT Google Sheets")
    
    # Update Google Sheets for ETHA
    print("\n📊 Attempting to update ETHA Google Sheets...")
    etha_sheets_manager = SheetsManager()
    
    if etha_sheets_manager.setup_sheets(Config.GOOGLE_WORKSHEET_ID_2):
        if etha_sheets_manager.upload_to_sheets(etha_table_data, etha_price, "ETHA"):
            print("✅ ETHA Google Sheets updated successfully")
        else:
            print("⚠️  ETHA Google Sheets update failed")
    else:
        print("⚠️  Continuing without ETHA Google Sheets")
    
    print(f"\n✅ Calculator completed")
    print(f"   IBIT Formula: BTC = IBIT ÷ {Config.BTC_PER_IBIT_RATIO}")
    print(f"   ETHA Formula: BTC = ETHA ÷ {Config.ETHA_RATIO:.10f}")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
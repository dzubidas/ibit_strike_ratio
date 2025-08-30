#!/usr/bin/env python3
"""
IBIT Strike to BTC Price Calculator with Google Sheets integration
Displays table with Strike Price and corresponding BTC hedge levels
"""

import requests
import json
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

# Google Sheets integration (optional)
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
        print("   Install with: pip install gspread google-auth")
        SHEETS_AVAILABLE = False
        return None, None

# Configuration
class Config:
    CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'service-account-key.json')
    SHEET_ID = os.getenv('GOOGLE_SHEET_ID', 'your_google_spreadsheet_id')
    WORKSHEET_ID = int(os.getenv('GOOGLE_WORKSHEET_ID', 'your_google_worksheet_id'))

class SheetsManager:
    """Google Sheets connection and data management"""
    
    def __init__(self):
        self.gc = None
        self.sheet = None
        self.worksheet = None
        self.gspread = None
        self.Credentials = None
        
    def setup_sheets(self):
        """Initialize Google Sheets connection with retry logic"""
        # Import modules when needed
        self.gspread, self.Credentials = import_sheets_modules()
        
        if not SHEETS_AVAILABLE:
            print("❌ Google Sheets libraries not available")
            return False
            
        if not os.path.exists(Config.CREDENTIALS_FILE):
            print(f"❌ Credentials file not found: {Config.CREDENTIALS_FILE}")
            return False
            
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = self.Credentials.from_service_account_file(Config.CREDENTIALS_FILE, scopes=scope)
                self.gc = self.gspread.authorize(creds)
                self.sheet = self.gc.open_by_key(Config.SHEET_ID)
                self.worksheet = self.sheet.get_worksheet_by_id(Config.WORKSHEET_ID)
                print("✅ Connected to Google Sheets")
                return True
                
            except Exception as e:
                print(f"❌ Sheets connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print("❌ All Google Sheets connection attempts failed")
                    return False
    
    def upload_to_sheets(self, table_data, ibit_price, btc_price, ratio):
        """Upload strike table data to Google Sheets"""
        if not self.worksheet:
            print("❌ No worksheet available for upload")
            return False
            
        try:
            # Clear existing data first
            print("📝 Clearing existing sheet data...")
            self.worksheet.clear()
            
            # Prepare header data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            header_data = [
                ['IBIT Strike to BTC Price Calculator'],
                [''],
                [f'Updated: {timestamp}'],
                [f'IBIT Price: ${ibit_price:,.2f}'],
                [f'BTC Price: ${btc_price:,.2f}'],
                [f'Ratio: {ratio:,.1f}'],
                [''],
                ['Strike Price', 'BTC Price']
            ]
            
            # Prepare table data
            table_rows = []
            for row in table_data:
                table_rows.append([
                    f'${row["strike"]:.2f}',
                    f'${row["btc_price"]:,.2f}'
                ])
            
            # Combine all data
            all_data = header_data + table_rows
            
            # Upload to sheets
            print("📊 Uploading data to Google Sheets...")
            self.worksheet.update('A1', all_data, value_input_option='USER_ENTERED')
            
            print(f"✅ Data uploaded to Google Sheets at {timestamp}")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading to Google Sheets: {e}")
            return False

def get_ibit_price():
    """Získa aktuálnu cenu IBIT z Yahoo Finance API"""
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

def get_btc_price():
    """Získa BTC index price z Kraken Futures API"""
    try:
        url = "https://futures.kraken.com/derivatives/api/v3/tickers/PF_XBTUSD"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Ubuntu) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Debug: print response structure (optional)
        # print(f"Debug - API response keys: {data.keys()}")
        
        # Handle different possible response structures
        tickers = None
        if 'result' in data:
            if isinstance(data['result'], dict):
                if 'tickers' in data['result']:
                    # Structure: {"result": {"tickers": [...]}}
                    tickers = data['result']['tickers']
                elif 'indexPrice' in data['result']:
                    # Direct structure: {"result": {"indexPrice": "..."}}
                    btc_price = float(data['result']['indexPrice'])
                    print(f"₿ BTC Price: ${btc_price:,.2f}")
                    return btc_price
                else:
                    # Structure: {"result": {"PF_XBTUSD": {"indexPrice": "..."}}}
                    if 'PF_XBTUSD' in data['result']:
                        btc_price = float(data['result']['PF_XBTUSD']['indexPrice'])
                        print(f"₿ BTC Price: ${btc_price:,.2f}")
                        return btc_price
            elif isinstance(data['result'], list):
                # Structure: {"result": [{"symbol": "PF_XBTUSD", ...}]}
                tickers = data['result']
        else:
            # Direct array structure
            tickers = data
        
        # Search in tickers array
        if tickers:
            for ticker in tickers:
                if ticker.get('symbol') == 'PF_XBTUSD':
                    btc_price = float(ticker['indexPrice'])
                    print(f"₿ BTC Price: ${btc_price:,.2f}")
                    return btc_price
        
        # Fallback to CoinGecko if Kraken fails
        print("⚠️  Kraken API structure unexpected, trying CoinGecko...")
        fallback_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        fallback_response = requests.get(fallback_url, timeout=10)
        fallback_data = fallback_response.json()
        btc_price = fallback_data['bitcoin']['usd']
        print(f"₿ BTC Price (CoinGecko): ${btc_price:,.2f}")
        return btc_price
        
    except Exception as e:
        print(f"❌ Error getting BTC price: {e}")
        return None

def calculate_strike_table(ibit_price, btc_price, strike_range=(25, 80)):
    """Vypočíta tabuľku strike prices a corresponding BTC levels"""
    ratio = btc_price / ibit_price
    
    table_data = []
    for strike in range(strike_range[0], strike_range[1] + 1):
        btc_hedge_level = strike * ratio
        table_data.append({
            'strike': strike,
            'btc_price': btc_hedge_level
        })
    
    print(f"📊 Generated {len(table_data)} strike price levels (Ratio: {ratio:,.1f})")
    return table_data, ratio

def print_table(table_data, ibit_price, btc_price, ratio):
    """Vypíše formatovanú tabuľku do terminálu"""
    # Clear terminal output first (optional)
    # print("\033[H\033[J", end="")
    
    # Header
    print("\n" + "=" * 80)
    print("IBIT STRIKE TO BTC PRICE CALCULATOR")
    print("=" * 80)
    print(f"IBIT Price: ${ibit_price:,.2f}")
    print(f"BTC Price:  ${btc_price:,.2f}")
    print(f"Ratio:      {ratio:,.1f}")
    print(f"Updated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Table header
    print(f"{'Strike Price':<15} | {'BTC Hedge Level':<15}")
    print("-" * 80)
    
    # Table rows
    for row in table_data:
        strike = row['strike']
        btc_price_level = row['btc_price']
        print(f"{strike:<14.2f} | ${btc_price_level:<14,.2f}")
    
    print("=" * 80)

def main():
    """Main function with optional Google Sheets integration"""
    print("🚀 Starting IBIT Strike to BTC Price Calculator...")
    print("📊 Fetching market data...")
    
    # Get current prices
    ibit_price = get_ibit_price()
    btc_price = get_btc_price()
    
    if not ibit_price or not btc_price:
        print(f"❌ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Failed to fetch market data")
        return 1
    
    # Calculate strike table
    table_data, ratio = calculate_strike_table(ibit_price, btc_price)
    
    # Print results to terminal
    print_table(table_data, ibit_price, btc_price, ratio)
    
    # Optional Google Sheets integration
    print("\n📈 Attempting to update Google Sheets...")
    sheets_manager = SheetsManager()
    
    if sheets_manager.setup_sheets():
        if sheets_manager.upload_to_sheets(table_data, ibit_price, btc_price, ratio):
            print("✅ Google Sheets updated successfully")
        else:
            print("⚠️  Google Sheets update failed, but calculation completed")
    else:
        print("⚠️  Continuing without Google Sheets integration")
    
    print("\n✅ IBIT Calculator completed successfully")
    return 0

def log_to_file(table_data, ibit_price, btc_price, ratio):
    """Optional: Save results to log file"""
    try:
        log_dir = os.path.dirname(os.path.abspath(__file__)) + "/logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'ibit_prices.log')
        
        with open(log_file, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp},IBIT:{ibit_price},BTC:{btc_price},RATIO:{ratio:.1f}\n")
        print(f"📝 Logged to {log_file}")
    except Exception as e:
        print(f"⚠️  Failed to write log file: {e}")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

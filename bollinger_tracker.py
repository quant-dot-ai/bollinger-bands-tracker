#!/usr/bin/env python3
"""
Indian Stock Bollinger Bands Tracker
Fetches stock data and updates Google Sheets with Bollinger Band analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import gspread
from google.oauth2.service_account import Credentials
import time
import logging
from typing import List, Dict, Tuple
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
class Config:
    # Bollinger Band settings
    BB_PERIOD = 200  # 200-day SMA
    BB_STD = 2      # 2 standard deviations
    
    # Google Sheets settings
    SPREADSHEET_NAME = "F&O New Addition"  # Your sheet name
    DAILY_SHEET = "Daily Bollinger Bands"
    HOURLY_SHEET = "Hourly Bollinger Bands"
    
    # Multiple stock sheets to process
    STOCK_SHEETS = ["Nifty50", "Smallcap100", "Midcap100"]
    
    # Batch settings
    BATCH_SIZE = 20
    DELAY_BETWEEN_REQUESTS = 0.5  # seconds
    
    # Add retry logic
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

class BollingerBandsTracker:
    def __init__(self, credentials_file: str):
        """Initialize the tracker with Google Sheets credentials"""
        self.setup_google_sheets(credentials_file)
        
    def setup_google_sheets(self, credentials_file: str):
        """Setup Google Sheets connection"""
        try:
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            # Authenticate
            creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
            self.client = gspread.authorize(creds)
            
            # Open spreadsheet
            self.spreadsheet = self.client.open(Config.SPREADSHEET_NAME)
            logging.info(f"Connected to Google Sheet: {Config.SPREADSHEET_NAME}")
            
        except Exception as e:
            logging.error(f"Failed to connect to Google Sheets: {e}")
            raise
    
    def get_stocks_by_sheet(self) -> Dict[str, List[str]]:
        """Get stocks organized by sheet name"""
        stocks_by_sheet = {}
        
        for sheet_name in Config.STOCK_SHEETS:
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                # Get all values from column A, starting from row 2
                stocks = worksheet.col_values(1)[1:]  # Skip header
                # Clean and filter
                stocks = [s.strip().upper() for s in stocks if s.strip()]
                # Add .NS suffix for Yahoo Finance
                stocks = [f"{s}.NS" for s in stocks]
                
                stocks_by_sheet[sheet_name] = stocks
                logging.info(f"Found {len(stocks)} stocks in {sheet_name}")
                
            except Exception as e:
                logging.warning(f"Could not read sheet {sheet_name}: {e}")
                stocks_by_sheet[sheet_name] = []
                continue
        
        return stocks_by_sheet
    
    def delete_sheet_if_exists(self, sheet_name: str):
        """Delete a worksheet if it exists"""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            self.spreadsheet.del_worksheet(worksheet)
            logging.info(f"Deleted existing sheet: {sheet_name}")
        except:
            # Sheet doesn't exist, which is fine
            pass
    
    def calculate_bollinger_bands(self, prices: pd.Series) -> Dict:
        """Calculate Bollinger Bands"""
        if len(prices) < Config.BB_PERIOD:
            return None
        
        # Calculate SMA
        sma = prices.rolling(window=Config.BB_PERIOD).mean()
        
        # Calculate standard deviation
        std = prices.rolling(window=Config.BB_PERIOD).std()
        
        # Calculate bands
        upper_band = sma + (Config.BB_STD * std)
        lower_band = sma - (Config.BB_STD * std)
        
        # Get latest values
        latest_idx = -1
        current_price = prices.iloc[latest_idx]
        sma_value = sma.iloc[latest_idx]
        upper_value = upper_band.iloc[latest_idx]
        lower_value = lower_band.iloc[latest_idx]
        
        # Calculate position (0-100%)
        if upper_value != lower_value:
            position = ((current_price - lower_value) / (upper_value - lower_value)) * 100
        else:
            position = 50
        
        # Determine signal
        if position > 95:
            signal = "🔴 Overbought"
        elif position > 80:
            signal = "🟡 Near Upper"
        elif position < 5:
            signal = "🟢 Oversold"
        elif position < 20:
            signal = "🟡 Near Lower"
        else:
            signal = "⚪ Neutral"
        
        return {
            'current_price': round(current_price, 2),
            'sma': round(sma_value, 2),
            'upper_band': round(upper_value, 2),
            'lower_band': round(lower_value, 2),
            'position': round(position, 1),
            'signal': signal
        }
    
    def fetch_daily_data(self, symbol: str) -> pd.DataFrame:
        """Fetch daily historical data with retry logic"""
        for retry in range(Config.MAX_RETRIES):
            try:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=400)  # Extra days for 200 trading days
                
                # Fetch data
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval="1d")
                
                if df.empty and retry < Config.MAX_RETRIES - 1:
                    logging.warning(f"No daily data found for {symbol}, retrying... ({retry + 1}/{Config.MAX_RETRIES})")
                    time.sleep(Config.RETRY_DELAY)
                    continue
                    
                return df
                
            except Exception as e:
                if retry < Config.MAX_RETRIES - 1:
                    logging.warning(f"Error fetching daily data for {symbol}: {e}, retrying... ({retry + 1}/{Config.MAX_RETRIES})")
                    time.sleep(Config.RETRY_DELAY)
                else:
                    logging.error(f"Failed to fetch daily data for {symbol} after {Config.MAX_RETRIES} attempts: {e}")
                    return None
        
        return None
    
    def fetch_hourly_data(self, symbol: str) -> pd.DataFrame:
        """Fetch hourly data (last 60 days max for Yahoo Finance)"""
        try:
            # Yahoo Finance limits: 60 days for hourly data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1h")
            
            if df.empty:
                logging.warning(f"No hourly data found for {symbol}")
                return None
                
            return df
            
        except Exception as e:
            logging.error(f"Error fetching hourly data for {symbol}: {e}")
            return None
    
    def process_daily_bollinger_bands(self, stocks: List[str]) -> List[List]:
        """Process daily Bollinger Bands for all stocks"""
        results = []
        
        for i, symbol in enumerate(stocks):
            try:
                logging.info(f"Processing daily data for {symbol} ({i+1}/{len(stocks)})")
                
                # Remove .NS for display
                display_symbol = symbol.replace('.NS', '')
                
                # Fetch data
                df = self.fetch_daily_data(symbol)
                if df is None or df.empty:
                    logging.warning(f"No daily data for {symbol}")
                    results.append([display_symbol, "No Data", "-", "-", "-", "-", "-", "-", "-"])
                    continue
                
                # Calculate Bollinger Bands
                bb = self.calculate_bollinger_bands(df['Close'])
                if bb is None:
                    logging.warning(f"Insufficient data for {symbol} (got {len(df)} days)")
                    results.append([display_symbol, "Insufficient Data", "-", "-", "-", "-", "-", "-", "-"])
                    continue
                
                # Calculate change %
                if len(df) > 1:
                    prev_close = df['Close'].iloc[-2]
                    change_pct = ((bb['current_price'] - prev_close) / prev_close) * 100
                else:
                    change_pct = 0
                
                # Get volume
                volume = df['Volume'].iloc[-1]
                volume_str = self.format_volume(volume)
                
                # Add to results
                results.append([
                    display_symbol,
                    bb['current_price'],
                    f"{change_pct:.2f}%",
                    bb['sma'],
                    bb['upper_band'],
                    bb['lower_band'],
                    bb['signal'],
                    f"{bb['position']:.1f}%",
                    volume_str
                ])
                
                logging.debug(f"Successfully processed {symbol}")
                
                # Delay to avoid rate limiting
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                logging.error(f"Error processing {symbol}: {str(e)}")
                results.append([display_symbol, "Error", "-", "-", "-", "-", "-", "-", str(e)[:50]])
        
        logging.info(f"Completed batch with {len(results)} results")
        return results
    
    def process_hourly_bollinger_bands(self, stocks: List[str]) -> List[List]:
        """Process hourly Bollinger Bands for all stocks"""
        results = []
        
        for i, symbol in enumerate(stocks):
            try:
                logging.info(f"Processing hourly data for {symbol} ({i+1}/{len(stocks)})")
                
                # Remove .NS for display
                display_symbol = symbol.replace('.NS', '')
                
                # Fetch data
                df = self.fetch_hourly_data(symbol)
                if df is None or df.empty:
                    results.append([display_symbol, "No Data", "-", "-", "-", "-", "-", "-", datetime.now().strftime("%Y-%m-%d %H:%M")])
                    continue
                
                # For hourly data with 200-period, we need to check if we have enough data
                if len(df) < Config.BB_PERIOD:
                    results.append([display_symbol, "Insufficient Data", "-", "-", "-", "-", "-", "-", datetime.now().strftime("%Y-%m-%d %H:%M")])
                    continue
                
                # Calculate Bollinger Bands
                bb = self.calculate_bollinger_bands(df['Close'])
                if bb is None:
                    results.append([display_symbol, "Calculation Error", "-", "-", "-", "-", "-", "-", datetime.now().strftime("%Y-%m-%d %H:%M")])
                    continue
                
                # Calculate change %
                if len(df) > Config.BB_PERIOD:
                    prev_close = df['Close'].iloc[-Config.BB_PERIOD-1]
                    change_pct = ((bb['current_price'] - prev_close) / prev_close) * 100
                else:
                    change_pct = 0
                
                # Add to results
                results.append([
                    display_symbol,
                    bb['current_price'],
                    f"{change_pct:.2f}%",
                    bb['sma'],
                    bb['upper_band'],
                    bb['lower_band'],
                    bb['signal'],
                    f"{bb['position']:.1f}%",
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ])
                
                # Delay to avoid rate limiting
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                logging.error(f"Error processing {symbol}: {e}")
                results.append([display_symbol, "Error", "-", "-", "-", "-", "-", "-", datetime.now().strftime("%Y-%m-%d %H:%M")])
        
        return results
    
    def format_volume(self, volume: float) -> str:
        """Format volume for display"""
        if volume >= 10000000:
            return f"{volume/10000000:.2f}Cr"
        elif volume >= 100000:
            return f"{volume/100000:.2f}L"
        elif volume >= 1000:
            return f"{volume/1000:.2f}K"
        else:
            return str(int(volume))
    
    def update_sheet(self, sheet_name: str, data: List[List], headers: List[str]):
        """Update Google Sheet with data (creates new sheet every time)"""
        try:
            # Always create a fresh worksheet
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            
            # Prepare all data to update at once
            all_data = []
            
            # Add title
            all_data.append([f'📊 {sheet_name}'])
            # Convert UTC to IST (UTC + 5:30)
            ist_timezone = timezone(timedelta(hours=5, minutes=30))
            ist_time = datetime.now(timezone.utc).astimezone(ist_timezone)
            all_data.append([f'Last Updated: {ist_time.strftime("%Y-%m-%d %H:%M:%S IST")}'])
            all_data.append([])  # Empty row
            all_data.append(headers)  # Headers
            
            # Add data rows - ensure all values are strings or numbers
            for row in data:
                cleaned_row = []
                for value in row:
                    if isinstance(value, (int, float)):
                        cleaned_row.append(value)
                    else:
                        cleaned_row.append(str(value))
                all_data.append(cleaned_row)
            
            # Update entire sheet at once
            if all_data:
                worksheet.update('A1', all_data)
            
            # Format headers (row 4)
            worksheet.format('A4:I4', {
                "backgroundColor": {"red": 0.26, "green": 0.52, "blue": 0.96},
                "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}
            })
            
            logging.info(f"Created and updated {sheet_name} with {len(data)} rows")
            
        except Exception as e:
            logging.error(f"Error updating sheet {sheet_name}: {e}")
            # Try to save data as CSV as backup
            try:
                import csv
                filename = f"{sheet_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(data)
                logging.info(f"Saved backup to {filename}")
            except Exception as backup_error:
                logging.error(f"Failed to save backup: {backup_error}")
    
    def run_daily_update(self):
        """Run daily Bollinger Bands update for each sheet separately"""
        logging.info("Starting daily Bollinger Bands update...")
        logging.info(f"Processing sheets: {', '.join(Config.STOCK_SHEETS)}")
        
        # Get stocks organized by sheet
        stocks_by_sheet = self.get_stocks_by_sheet()
        
        # Check if any stocks were found
        total_stocks = sum(len(stocks) for stocks in stocks_by_sheet.values())
        if total_stocks == 0:
            logging.error("No stocks found in any sheet! Please check your Google Sheet has the required sheets: " + ", ".join(Config.STOCK_SHEETS))
            return
        
        # Process each sheet separately
        for sheet_name, stocks in stocks_by_sheet.items():
            if not stocks:
                logging.warning(f"No stocks found in {sheet_name}, skipping...")
                continue
            
            output_sheet_name = f"{sheet_name} Daily BB"
            logging.info(f"\nProcessing {sheet_name} with {len(stocks)} stocks...")
            
            # Delete existing sheet to ensure clean data
            self.delete_sheet_if_exists(output_sheet_name)
            
            # Process in batches
            all_results = []
            for i in range(0, len(stocks), Config.BATCH_SIZE):
                batch = stocks[i:i + Config.BATCH_SIZE]
                logging.info(f"Processing {sheet_name} batch {i//Config.BATCH_SIZE + 1}/{(len(stocks)-1)//Config.BATCH_SIZE + 1}")
                
                try:
                    results = self.process_daily_bollinger_bands(batch)
                    all_results.extend(results)
                except Exception as e:
                    logging.error(f"Error in batch processing for {sheet_name}: {e}")
                    # Continue with next batch even if this one fails
                    continue
            
            # Update sheet only if we have results
            if all_results:
                headers = ['Stock', 'Current Price', 'Change %', 'SMA(200)', 'Upper Band', 
                          'Lower Band', 'Signal', 'Position', 'Volume']
                self.update_sheet(output_sheet_name, all_results, headers)
            else:
                logging.error(f"No results to save for {sheet_name} Daily BB")
        
        logging.info("\nAll daily updates complete!")
    
    def run_hourly_update(self):
        """Run hourly Bollinger Bands update for each sheet separately"""
        logging.info("Starting hourly Bollinger Bands update...")
        logging.info(f"Processing sheets: {', '.join(Config.STOCK_SHEETS)}")
        
        # Get stocks organized by sheet
        stocks_by_sheet = self.get_stocks_by_sheet()
        
        # Check if any stocks were found
        total_stocks = sum(len(stocks) for stocks in stocks_by_sheet.values())
        if total_stocks == 0:
            logging.error("No stocks found in any sheet! Please check your Google Sheet has the required sheets: " + ", ".join(Config.STOCK_SHEETS))
            return
        
        # Process each sheet separately
        for sheet_name, stocks in stocks_by_sheet.items():
            if not stocks:
                logging.warning(f"No stocks found in {sheet_name}, skipping...")
                continue
            
            output_sheet_name = f"{sheet_name} Hourly BB"
            logging.info(f"\nProcessing {sheet_name} with {len(stocks)} stocks...")
            
            # Delete existing sheet to ensure clean data
            self.delete_sheet_if_exists(output_sheet_name)
            
            # Process in batches
            all_results = []
            for i in range(0, len(stocks), Config.BATCH_SIZE):
                batch = stocks[i:i + Config.BATCH_SIZE]
                logging.info(f"Processing {sheet_name} batch {i//Config.BATCH_SIZE + 1}/{(len(stocks)-1)//Config.BATCH_SIZE + 1}")
                results = self.process_hourly_bollinger_bands_simple(batch)
                all_results.extend(results)
            
            # Update sheet with simplified headers
            headers = ['Stock', 'Current Price', 'Lower Band', 'SMA(200)', 'Upper Band']
            self.update_sheet(output_sheet_name, all_results, headers)
        
        logging.info("\nAll hourly updates complete!")
    
    def process_hourly_bollinger_bands_simple(self, stocks: List[str]) -> List[List]:
        """Process hourly Bollinger Bands with just essential data"""
        results = []
        
        for i, symbol in enumerate(stocks):
            try:
                logging.info(f"Processing hourly data for {symbol} ({i+1}/{len(stocks)})")
                
                # Remove .NS for display
                display_symbol = symbol.replace('.NS', '')
                
                # Fetch data
                df = self.fetch_hourly_data(symbol)
                if df is None or df.empty:
                    results.append([display_symbol, "No Data", "-", "-", "-"])
                    continue
                
                # For hourly data with 200-period, we need to check if we have enough data
                if len(df) < Config.BB_PERIOD:
                    results.append([display_symbol, "Insufficient Data", "-", "-", "-"])
                    continue
                
                # Calculate Bollinger Bands
                bb = self.calculate_bollinger_bands(df['Close'])
                if bb is None:
                    results.append([display_symbol, "Calculation Error", "-", "-", "-"])
                    continue
                
                # Add to results - just the essential data
                results.append([
                    display_symbol,
                    bb['current_price'],
                    bb['lower_band'],
                    bb['sma'],
                    bb['upper_band']
                ])
                
                # Delay to avoid rate limiting
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                logging.error(f"Error processing {symbol}: {e}")
                results.append([display_symbol, "Error", "-", "-", "-"])
        
        return results

def main():
    """Main function"""
    # You need to set up Google Sheets API credentials
    # Download the credentials JSON file from Google Cloud Console
    CREDENTIALS_FILE = "credentials.json"
    
    # Check if credentials file exists, if not running in GitHub Actions
    if not os.path.exists(CREDENTIALS_FILE):
        logging.error(f"Credentials file {CREDENTIALS_FILE} not found!")
        logging.info("Make sure credentials.json is in the same directory as this script")
        return
    
    # Initialize tracker
    tracker = BollingerBandsTracker(CREDENTIALS_FILE)
    
    # Run updates
    tracker.run_daily_update()
    tracker.run_hourly_update()  # Added hourly update

if __name__ == "__main__":
    main()
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Indian Stock Bollinger Bands Tracker that fetches stock data from Yahoo Finance and updates Google Sheets with Bollinger Band analysis. The system processes multiple stock lists (Nifty50, Smallcap100, Midcap100) and generates both daily and hourly Bollinger Band reports.

## Development Commands

### Running the Application
- **Primary execution**: `./RUN_STOCK_TRACKER.command` (macOS/Linux) or `RUN_STOCK_TRACKER.bat` (Windows)
- **Simple run**: `python simple_run.py` (uses existing virtual environment)
- **Direct execution**: `source venv/bin/activate && python bollinger_tracker.py`

### Virtual Environment
- The project uses a pre-configured virtual environment in `venv/`
- Activate: `source venv/bin/activate`
- Deactivate: `deactivate`
- Dependencies are already installed (see pip list output for installed packages)

## Architecture

### Core Components

1. **BollingerBandsTracker Class** (`bollinger_tracker.py:46-521`)
   - Main application class that orchestrates the entire process
   - Handles Google Sheets integration, data fetching, and Bollinger Band calculations

2. **Configuration** (`bollinger_tracker.py:25-44`)
   - `Config` class contains all configuration settings
   - Key settings: BB_PERIOD=200, BB_STD=2, batch processing settings
   - Multiple stock sheet names: Nifty50, Smallcap100, Midcap100

3. **Data Processing Pipeline**
   - `get_stocks_by_sheet()`: Reads stock symbols from Google Sheets
   - `fetch_daily_data()`/`fetch_hourly_data()`: Retrieves data from Yahoo Finance
   - `calculate_bollinger_bands()`: Performs BB calculations (200-day SMA, ±2 std dev)
   - `process_daily_bollinger_bands()`/`process_hourly_bollinger_bands()`: Batch processing
   - `update_sheet()`: Creates new worksheets with results

### Key Features
- **Batch Processing**: Processes stocks in configurable batches (default: 20)
- **Rate Limiting**: 0.5-second delay between requests to avoid API limits
- **Retry Logic**: 3 retry attempts with 2-second delays
- **Error Handling**: Comprehensive error handling with fallback to CSV export
- **Signal Generation**: Categorizes positions as Overbought, Oversold, Near Upper/Lower, or Neutral

### Google Sheets Integration
- Uses service account authentication via `credentials.json`
- Creates separate sheets for each stock list (e.g., "Nifty50 Daily BB", "Midcap100 Hourly BB")
- Always creates fresh worksheets (deletes existing ones) for clean data

### Data Output Structure
**Daily Reports**: Stock, Current Price, Change %, SMA(200), Upper Band, Lower Band, Signal, Position, Volume
**Hourly Reports**: Stock, Current Price, Lower Band, SMA(200), Upper Band

## Dependencies

Key packages (from venv):
- `yfinance`: Stock data fetching
- `pandas`/`numpy`: Data manipulation and calculations  
- `gspread`/`google-auth`: Google Sheets API integration
- `requests`: HTTP requests

## File Structure
- `bollinger_tracker.py`: Main application logic
- `simple_run.py`: Simplified runner script
- `RUN_STOCK_TRACKER.command`/`.bat`: Platform-specific launchers
- `credentials.json`: Google Sheets service account credentials (required)
- `venv/`: Pre-configured Python virtual environment
- CSV output files: Backup exports with timestamps

## Development Notes
- Stock symbols are automatically appended with `.NS` for Yahoo Finance (Indian market)
- The system processes 200-period Bollinger Bands which requires sufficient historical data
- Hourly data is limited to 60 days by Yahoo Finance API constraints
- All timestamps and calculations use local system time
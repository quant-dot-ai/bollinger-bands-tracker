# Indian Stock Bollinger Bands Tracker

A Python application that fetches Indian stock market data and updates Google Sheets with Bollinger Band analysis for multiple stock indices.

## Features

- 📊 **Multi-Index Support**: Tracks Nifty50, Smallcap100, and Midcap100 stocks
- 📈 **Bollinger Band Analysis**: 200-period SMA with ±2 standard deviation bands
- ⏰ **Dual Timeframes**: Both daily and hourly analysis
- 📋 **Google Sheets Integration**: Automatic updates to shared spreadsheets
- 🔄 **Batch Processing**: Efficient handling of large stock lists
- 🛡️ **Error Handling**: Comprehensive retry logic and CSV backups

## Quick Start

### Prerequisites
- Python 3.x
- Google Sheets API credentials (service account)
- Internet connection

### Setup
1. Clone this repository
2. Ensure you have `credentials.json` from Google Cloud Console
3. Make sure the virtual environment (`venv/`) is properly set up

### Running the Application

**Easy Run (Recommended)**:
- macOS/Linux: `./RUN_STOCK_TRACKER.command`
- Windows: `RUN_STOCK_TRACKER.bat`

**Alternative**:
```bash
python simple_run.py
```

**Manual**:
```bash
source venv/bin/activate
python bollinger_tracker.py
```

## Configuration

The application is configured via the `Config` class in `bollinger_tracker.py`:

- **Bollinger Bands**: 200-day period, ±2 standard deviations
- **Stock Lists**: Reads from "Nifty50", "Smallcap100", "Midcap100" sheets
- **Output Sheets**: Creates separate daily and hourly BB sheets for each index
- **Batch Size**: Processes 20 stocks at a time
- **Rate Limiting**: 0.5-second delay between API calls

## Output

### Daily Reports
Contains: Stock Symbol, Current Price, Change %, SMA(200), Upper Band, Lower Band, Signal, Position %, Volume

### Hourly Reports
Contains: Stock Symbol, Current Price, Lower Band, SMA(200), Upper Band

### Signals
- 🔴 **Overbought**: Position > 95%
- 🟡 **Near Upper**: Position 80-95%
- ⚪ **Neutral**: Position 20-80%
- 🟡 **Near Lower**: Position 5-20%
- 🟢 **Oversold**: Position < 5%

## Data Sources

- **Stock Data**: Yahoo Finance (yfinance)
- **Stock Lists**: Google Sheets (configurable spreadsheet)
- **Output**: Google Sheets with automatic worksheet creation

## Dependencies

Key packages (installed in venv):
- `yfinance`: Stock data fetching
- `pandas`, `numpy`: Data processing
- `gspread`, `google-auth`: Google Sheets API
- Other standard data science libraries

## Important Notes

- Requires `credentials.json` for Google Sheets access
- Stock symbols automatically get `.NS` suffix for Indian market
- 200-period requirement means sufficient historical data is needed
- Hourly data limited to 60 days by Yahoo Finance
- Creates fresh worksheets on each run (overwrites existing data)
- CSV backups created automatically on sheet update failures

## Troubleshooting

1. **"No credentials.json"**: Ensure the file is in the root directory
2. **"Permission denied"**: Check if Google Sheet is shared with service account email
3. **"Insufficient data"**: Stock may not have enough historical data for 200-period calculation
4. **Rate limiting**: Built-in delays and retry logic handle most API limits

For detailed development guidance, see `CLAUDE.md`.
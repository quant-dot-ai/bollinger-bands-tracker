#!/usr/bin/env python3
"""
STOCK TRACKER - Uses existing venv
"""

import os
import sys
import subprocess

print("\n🚀 Starting Stock Tracker...")
print("📊 This will update your Google Sheet with latest data")
print("⏳ Please wait about 2-3 minutes...\n")

try:
    # Import and run the main tracker
    import bollinger_tracker
    
    # Update credentials path to same folder
    bollinger_tracker.CREDENTIALS_FILE = "credentials.json"
    
    # Run the tracker
    tracker = bollinger_tracker.BollingerBandsTracker(bollinger_tracker.CREDENTIALS_FILE)
    tracker.run_daily_update()
    tracker.run_hourly_update()
    
    print("\n✅ SUCCESS! Your Google Sheet has been updated!")
    print("📈 Check your 'Daily Bollinger Bands' and 'Hourly Bollinger Bands' sheets")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print("\nPlease check:")
    print("1. credentials.json is in this folder")
    print("2. Your internet connection")
    print("3. The Google Sheet is shared with the service account email")

input("\n📌 Press Enter to close...")
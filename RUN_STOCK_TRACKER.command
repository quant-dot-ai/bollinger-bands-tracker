#!/bin/bash
clear
echo "===================================="
echo "    STOCK TRACKER - BOLLINGER BANDS"
echo "===================================="
echo ""

# Navigate to the script directory
cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "Please make sure 'venv' folder exists in this directory"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

echo "📦 Using virtual environment..."
echo ""

# Activate virtual environment and run
source venv/bin/activate
python bollinger_tracker.py
deactivate

echo ""
echo "✅ Update complete! Check your Google Sheets"
echo ""
echo "Press any key to close..."
read -n 1
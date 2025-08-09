# Setting up GitHub Repository Secret for Google Sheets

To enable automated runs, you need to add your Google Sheets credentials as a repository secret.

## Steps:

1. **Go to your repository**: https://github.com/quant-dot-ai/bollinger-bands-tracker

2. **Navigate to Settings**:
   - Click on "Settings" tab in your repository
   - Click on "Secrets and variables" in the left sidebar
   - Click on "Actions"

3. **Create New Repository Secret**:
   - Click "New repository secret"
   - **Name**: `GOOGLE_CREDENTIALS`
   - **Secret**: Copy and paste the entire contents of your `credentials.json` file

4. **Save**: Click "Add secret"

## How it works:

The GitHub Action workflow will:
- Run every hour during Indian market hours (9:15 AM - 3:30 PM IST)
- Only run on weekdays (Monday-Friday)
- Create the credentials file temporarily during execution
- Clean up the credentials file after completion
- Can also be triggered manually for testing

## Schedule Details:

- **Market Hours**: 9:15 AM - 3:30 PM IST (Monday-Friday)
- **UTC Schedule**: 3:45 AM - 10:00 AM UTC (accounting for IST = UTC+5:30)
- **Frequency**: Every hour during market hours
- **Days**: Weekdays only (excludes weekends and holidays)

## Testing:

After setting up the secret, you can:
1. Go to "Actions" tab in your repository
2. Click on "Indian Stock Market Tracker" workflow
3. Click "Run workflow" to test manually
4. Check the logs to ensure it's working correctly

## Note:

The workflow will automatically handle:
- Installing Python dependencies
- Creating/cleaning up credentials
- Running both daily and hourly updates
- Logging completion status
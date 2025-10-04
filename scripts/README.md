# Payment Reminder Scripts

This directory contains scripts for automatically running payment reminder notifications.

## Files

### 1. `daily_payment_reminders.sh`
Bash script that runs the payment reminder command and logs output.

**Features:**
- Runs `python manage.py check_payment_dues --days-ahead 3`
- Logs all output with timestamps
- Error handling and logging
- Creates log directory automatically

### 2. `payment_scheduler.py` 
Python script using schedule library for advanced scheduling.

**Features:**
- Daily payment reminders at 9:00 AM
- Weekly cleanup on Sundays at 2:00 AM  
- Homework reminders on weekdays at 8:00 AM
- Comprehensive logging
- Runs continuously

**Requirements:**
```bash
pip install schedule
```

### 3. `setup_cron.sh`
Setup script that automatically configures cron jobs.

**Features:**
- Makes scripts executable
- Adds cron job for daily execution
- Checks for existing cron jobs
- Shows current cron configuration

## Quick Setup

### Option 1: Simple Cron Job (Recommended)

```bash
# Make setup script executable
chmod +x scripts/setup_cron.sh

# Run setup (adds daily cron job at 9 AM)
./scripts/setup_cron.sh
```

### Option 2: Manual Cron Setup

```bash
# Make script executable
chmod +x scripts/daily_payment_reminders.sh

# Edit crontab
crontab -e

# Add this line for daily execution at 9 AM:
0 9 * * * /Volumes/Transcend/backend/codeschool_backend/scripts/daily_payment_reminders.sh
```

### Option 3: Python Scheduler (Advanced)

```bash
# Install required package
pip install schedule

# Run the Python scheduler (runs continuously)
python scripts/payment_scheduler.py
```

## Configuration

### Customize Script Paths

Edit the variables in `daily_payment_reminders.sh`:

```bash
PROJECT_DIR="/your/project/path"
PYTHON_PATH="/your/python/path"
```

### Customize Schedule

Edit cron timing (format: minute hour day month weekday):

```bash
# Daily at 9 AM
0 9 * * *

# Every Monday at 9 AM  
0 9 * * 1

# Twice daily (9 AM and 6 PM)
0 9,18 * * *
```

### Customize Command Options

Modify the command in the script:

```bash
# Check 7 days ahead instead of 3
python manage.py check_payment_dues --days-ahead 7

# Dry run only (no actual notifications)
python manage.py check_payment_dues --dry-run
```

## Logging

### Log Location
```
/Volumes/Transcend/backend/codeschool_backend/logs/payment_reminders.log
```

### Log Format
```
[2025-10-04 09:00:01] Starting daily payment reminder check...
[2025-10-04 09:00:02] SUCCESS: Payment reminders completed successfully
[2025-10-04 09:00:02] Output: Successfully sent 3 payment notifications
[2025-10-04 09:00:02] Payment reminder check completed
----------------------------------------
```

### View Logs
```bash
# View recent logs
tail -f logs/payment_reminders.log

# View last 50 lines
tail -50 logs/payment_reminders.log

# Search for errors
grep "ERROR" logs/payment_reminders.log
```

## Troubleshooting

### Check if Cron Job is Running
```bash
# List current cron jobs
crontab -l

# Check cron service status (Ubuntu/Debian)
sudo systemctl status cron

# Check cron service status (macOS)
sudo launchctl list | grep cron
```

### Test Script Manually
```bash
# Run script manually to test
./scripts/daily_payment_reminders.sh

# Check if command works
cd /your/project && python manage.py check_payment_dues --dry-run
```

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x scripts/daily_payment_reminders.sh
   ```

2. **Python Path Issues**
   ```bash
   # Find your Python path
   which python
   
   # Update PYTHON_PATH in script
   ```

3. **Django Settings**
   ```bash
   # Make sure DJANGO_SETTINGS_MODULE is set correctly
   export DJANGO_SETTINGS_MODULE=core.settings
   ```

4. **Cron Environment**
   ```bash
   # Add environment variables to crontab
   crontab -e
   
   # Add at top:
   PATH=/usr/local/bin:/usr/bin:/bin
   DJANGO_SETTINGS_MODULE=core.settings
   ```

## What You'll Get

### Daily Notifications

**Upcoming Payments:**
```
Title: Payment Due Soon: John Doe
Message: Payment for John Doe in Group A is due on October 15th. 
         Amount: $450.00 (Period: 10/2025)
```

**Overdue Payments:**
```
Title: OVERDUE PAYMENT: Jane Smith  
Message: Payment for Jane Smith in Group B is 5 days overdue!
         Due date: October 1st. Amount: $500.00 (Period: 10/2025).
         Please contact immediately!
```

### Log Entries
```
[2025-10-04 09:00:01] Starting daily payment reminder check...
[2025-10-04 09:00:02] SUCCESS: Payment reminders completed successfully
[2025-10-04 09:00:02] Output: Successfully sent 3 payment notifications
```

## Stopping/Removing

### Remove Cron Job
```bash
# Edit crontab
crontab -e

# Delete the line containing 'daily_payment_reminders.sh'
# Save and exit
```

### Stop Python Scheduler
```bash
# Press Ctrl+C in the terminal running payment_scheduler.py
```

## Advanced Configuration

### Multiple Schedules
```bash
# Different schedules for different checks
0 9 * * * /path/to/scripts/daily_payment_reminders.sh
0 18 * * 5 /path/to/scripts/weekly_payment_summary.sh
```

### Email Notifications
Add email notification to script:
```bash
# Add to script after successful run
echo "Payment reminders sent successfully" | mail -s "Daily Payment Check" admin@yourschool.com
```
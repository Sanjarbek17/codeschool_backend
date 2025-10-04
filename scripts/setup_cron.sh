#!/bin/bash

# Setup script for payment reminder scheduling
# This script sets up cron jobs for automatic payment reminders

PROJECT_DIR="/Volumes/Transcend/backend/codeschool_backend"
SCRIPT_DIR="$PROJECT_DIR/scripts"

echo "Setting up payment reminder scheduling..."

# Make scripts executable
chmod +x "$SCRIPT_DIR/daily_payment_reminders.sh"

# Create cron job entry
CRON_ENTRY="0 9 * * * $SCRIPT_DIR/daily_payment_reminders.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_payment_reminders.sh"; then
    echo "Cron job already exists!"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "Cron job added successfully!"
fi

echo "Current cron jobs:"
crontab -l

echo ""
echo "Setup complete! Payment reminders will run daily at 9:00 AM"
echo "Log file location: $PROJECT_DIR/logs/payment_reminders.log"
echo ""
echo "To remove the cron job later, run:"
echo "crontab -e"
echo "and delete the line containing 'daily_payment_reminders.sh'"
#!/bin/bash

# Daily Payment Reminder Script
# This script runs the payment reminder command automatically

# Configuration
PROJECT_DIR="/Volumes/Transcend/backend/codeschool_backend"
PYTHON_PATH="/Users/sanjarbeksaidov/.pyenv/versions/3.13.5/bin/python"  # Adjust to your Python path
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/payment_reminders.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to run payment reminders
run_payment_reminders() {
    log_message "Starting daily payment reminder check..."
    
    cd "$PROJECT_DIR" || {
        log_message "ERROR: Could not change to project directory: $PROJECT_DIR"
        exit 1
    }
    
    # Run the command and capture output
    OUTPUT=$("$PYTHON_PATH" manage.py check_payment_dues --days-ahead 3 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_message "SUCCESS: Payment reminders completed successfully"
        log_message "Output: $OUTPUT"
    else
        log_message "ERROR: Payment reminders failed with exit code $EXIT_CODE"
        log_message "Error output: $OUTPUT"
    fi
    
    log_message "Payment reminder check completed"
    echo "----------------------------------------" >> "$LOG_FILE"
}

# Main execution
echo "Daily Payment Reminder Script Starting..."
run_payment_reminders
echo "Script completed. Check log file: $LOG_FILE"
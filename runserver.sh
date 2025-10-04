#!/bin/bash

# Enhanced runserver script with notification scheduler options
# CodeSchool Backend Server Startup

PROJECT_DIR="$(pwd)"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    CodeSchool Backend Server Setup    ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to setup cron job
setup_cron_job() {
    echo -e "${YELLOW}Setting up daily payment reminder cron job...${NC}"
    if [ -f "$SCRIPTS_DIR/setup_cron.sh" ]; then
        bash "$SCRIPTS_DIR/setup_cron.sh"
    else
        echo -e "${RED}Error: setup_cron.sh not found in scripts directory${NC}"
    fi
    echo ""
}

# Function to run Python scheduler in background
run_python_scheduler() {
    echo -e "${YELLOW}Starting Python scheduler in background...${NC}"
    
    # Check if schedule package is installed
    if ! python -c "import schedule" 2>/dev/null; then
        echo -e "${RED}Schedule package not installed. Installing...${NC}"
        pip install schedule
    fi
    
    if [ -f "$SCRIPTS_DIR/payment_scheduler.py" ]; then
        echo -e "${GREEN}Starting scheduler in background...${NC}"
        nohup python "$SCRIPTS_DIR/payment_scheduler.py" > logs/scheduler.log 2>&1 &
        SCHEDULER_PID=$!
        echo -e "${GREEN}Scheduler started with PID: $SCHEDULER_PID${NC}"
        echo "$SCHEDULER_PID" > logs/scheduler.pid
    else
        echo -e "${RED}Error: payment_scheduler.py not found in scripts directory${NC}"
    fi
    echo ""
}

# Function to demo signal-based notifications
demo_signal_notifications() {
    echo -e "${YELLOW}Running signal-based notification demo...${NC}"
    if [ -f "$SCRIPTS_DIR/demo_signals.py" ]; then
        python "$SCRIPTS_DIR/demo_signals.py"
    else
        echo -e "${RED}Error: demo_signals.py not found in scripts directory${NC}"
    fi
    echo ""
}

# Function to trigger manual payment check via signals
trigger_signal_check() {
    echo -e "${YELLOW}Triggering manual payment check via signals...${NC}"
    python manage.py trigger_payment_signals --verbose
    echo ""
}

# Function to test payment reminders
test_payment_reminders() {
    echo -e "${YELLOW}Testing payment reminder system...${NC}"
    python manage.py check_payment_dues --dry-run
    echo ""
}

# Function to check existing cron jobs
check_cron_status() {
    echo -e "${YELLOW}Current cron jobs:${NC}"
    crontab -l 2>/dev/null | grep -E "(payment|reminder)" || echo "No payment reminder cron jobs found"
    echo ""
}

# Menu function
show_menu() {
    echo -e "${GREEN}Choose notification setup option:${NC}"
    echo ""
    echo "1) Setup daily cron job (9 AM daily) - REQUIRES CRON SUPPORT"
    echo "2) Run Python scheduler in background - REQUIRES BACKGROUND PROCESS"
    echo "3) Use signal-based notifications (RECOMMENDED) - NO SCHEDULING NEEDED"
    echo "4) Demo signal-based notifications"
    echo "5) Test payment reminders (dry run)"
    echo "6) Check current cron jobs"
    echo "7) Skip notification setup"
    echo ""
    echo -n "Enter your choice (1-7): "
}

# Main menu loop
while true; do
    show_menu
    read choice
    echo ""
    
    case $choice in
        1)
            setup_cron_job
            break
            ;;
        2)
            run_python_scheduler
            break
            ;;
        3)
            echo -e "${GREEN}✅ Signal-based notifications are now active!${NC}"
            echo -e "${BLUE}Notifications will trigger automatically on these events:${NC}"
            echo -e "${BLUE}  • Payment creation/updates${NC}"
            echo -e "${BLUE}  • Homework assignments${NC}"
            echo -e "${BLUE}  • Student submissions${NC}"
            echo -e "${BLUE}  • Progress updates${NC}"
            echo ""
            echo -e "${YELLOW}Manual trigger available via:${NC}"
            echo -e "${YELLOW}  API: POST /api/notifications/trigger_payment_check/${NC}"
            echo -e "${YELLOW}  CLI: python manage.py trigger_payment_signals${NC}"
            echo ""
            trigger_signal_check
            break
            ;;
        4)
            demo_signal_notifications
            ;;
        5)
            test_payment_reminders
            ;;
        6)
            check_cron_status
            ;;
        7)
            echo -e "${BLUE}Skipping notification setup...${NC}"
            echo ""
            break
            ;;
        *)
            echo -e "${RED}Invalid option. Please choose 1-7.${NC}"
            echo ""
            ;;
    esac
done

# Start the Django server
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}       Starting Django Server          ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Server will be available at:${NC}"
echo -e "${BLUE}  Local:   http://localhost:8000${NC}"
echo -e "${BLUE}  Network: http://0.0.0.0:8000${NC}"
echo ""
echo -e "${BLUE}API Documentation:${NC}"
echo -e "${BLUE}  Swagger: http://localhost:8000/swagger/${NC}"
echo -e "${BLUE}  ReDoc:   http://localhost:8000/redoc/${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the Django development server
python manage.py runserver 0.0.0.0:8000
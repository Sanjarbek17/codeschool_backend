#!/bin/bash

# Cleanup script for CodeSchool Backend
# Stops background processes and cleans up

PROJECT_DIR="$(pwd)"
LOGS_DIR="$PROJECT_DIR/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}CodeSchool Backend Cleanup${NC}"
echo "=========================="

# Stop Python scheduler if running
if [ -f "$LOGS_DIR/scheduler.pid" ]; then
    SCHEDULER_PID=$(cat "$LOGS_DIR/scheduler.pid")
    if ps -p $SCHEDULER_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Python scheduler (PID: $SCHEDULER_PID)...${NC}"
        kill $SCHEDULER_PID
        rm "$LOGS_DIR/scheduler.pid"
        echo -e "${GREEN}Scheduler stopped${NC}"
    else
        echo -e "${YELLOW}Scheduler not running${NC}"
        rm -f "$LOGS_DIR/scheduler.pid"
    fi
else
    echo -e "${YELLOW}No scheduler PID file found${NC}"
fi

# Show current cron jobs
echo ""
echo -e "${YELLOW}Current cron jobs:${NC}"
crontab -l 2>/dev/null | grep -E "(payment|reminder)" || echo "No payment reminder cron jobs found"

# Option to remove cron job
echo ""
echo -n "Remove payment reminder cron job? (y/n): "
read remove_cron

if [ "$remove_cron" = "y" ] || [ "$remove_cron" = "Y" ]; then
    # Remove the cron job
    crontab -l 2>/dev/null | grep -v "daily_payment_reminders.sh" | crontab -
    echo -e "${GREEN}Cron job removed${NC}"
fi

echo ""
echo -e "${GREEN}Cleanup completed${NC}"
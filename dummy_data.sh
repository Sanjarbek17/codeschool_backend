#!/bin/bash

# CodeSchool Backend Dummy Data Commands
# This script provides shortcuts for commonly used dummy data commands

echo "🎓 CodeSchool Backend Dummy Data Commands"
echo "========================================"
echo

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the Django project root directory"
    exit 1
fi

# Define Python command
PYTHON_CMD="./env/bin/python"

if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python"
fi

# Function to run command with proper error handling
run_command() {
    echo "🔄 Running: $1"
    if eval "$1"; then
        echo "✅ Success!"
    else
        echo "❌ Failed!"
        exit 1
    fi
    echo
}

# Parse command line arguments
case "$1" in
    "help"|"--help"|"-h"|"")
        echo "Available commands:"
        echo
        echo "📊 DATA CREATION:"
        echo "  ./dummy_data.sh create-all         # Create all dummy data (default amounts)"
        echo "  ./dummy_data.sh create-small       # Create small dataset for testing"
        echo "  ./dummy_data.sh create-large       # Create large dataset"
        echo
        echo "🗑️  DATA CLEANUP:"
        echo "  ./dummy_data.sh clean              # Clean all data (with confirmation)"
        echo "  ./dummy_data.sh clean-keep-admin   # Clean all data but keep admin users"
        echo
        echo "🔍 INDIVIDUAL APPS:"
        echo "  ./dummy_data.sh accounts           # Create only accounts data"
        echo "  ./dummy_data.sh courses            # Create only courses data"
        echo "  ./dummy_data.sh assignments        # Create only assignments data"
        echo "  ./dummy_data.sh submissions        # Create only submissions data"
        echo "  ./dummy_data.sh progress           # Create only progress data"
        echo
        echo "📋 INFORMATION:"
        echo "  ./dummy_data.sh list               # List all available Django commands"
        echo "  ./dummy_data.sh status             # Show current database status"
        echo
        ;;
    "create-all")
        echo "Creating complete dummy dataset..."
        run_command "$PYTHON_CMD manage.py create_all_dummy_data"
        ;;
    "create-small")
        echo "Creating small test dataset..."
        run_command "$PYTHON_CMD manage.py create_all_dummy_data --teachers 3 --students 15 --groups 2 --lessons 5 --homework 8 --tasks 20 --submissions 30 --test-cases 25 --attendance-records 40 --homework-progress 20 --task-progress 50"
        ;;
    "create-large")
        echo "Creating large dataset..."
        run_command "$PYTHON_CMD manage.py create_all_dummy_data --teachers 25 --students 200 --groups 10 --lessons 50 --homework 80 --tasks 300 --submissions 800 --test-cases 400 --attendance-records 500 --homework-progress 400 --task-progress 1000"
        ;;
    "clean")
        echo "⚠️  WARNING: This will delete ALL data from the database!"
        echo "Are you sure you want to continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            run_command "$PYTHON_CMD manage.py clean_all_dummy_data --confirm"
        else
            echo "Cancelled."
        fi
        ;;
    "clean-keep-admin")
        echo "⚠️  WARNING: This will delete all data except superuser accounts!"
        echo "Are you sure you want to continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            run_command "$PYTHON_CMD manage.py clean_all_dummy_data --confirm --keep-superusers"
        else
            echo "Cancelled."
        fi
        ;;
    "accounts")
        echo "Creating accounts dummy data..."
        run_command "$PYTHON_CMD manage.py create_accounts_dummy_data"
        ;;
    "courses")
        echo "Creating courses dummy data..."
        run_command "$PYTHON_CMD manage.py create_courses_dummy_data"
        ;;
    "assignments")
        echo "Creating assignments dummy data..."
        run_command "$PYTHON_CMD manage.py create_assignments_dummy_data"
        ;;
    "submissions")
        echo "Creating submissions dummy data..."
        run_command "$PYTHON_CMD manage.py create_submissions_dummy_data"
        ;;
    "progress")
        echo "Creating progress dummy data..."
        run_command "$PYTHON_CMD manage.py create_progress_dummy_data"
        ;;
    "list")
        echo "Available Django management commands:"
        echo
        $PYTHON_CMD manage.py help
        ;;
    "status")
        echo "Database status:"
        echo "==============="
        $PYTHON_CMD manage.py shell -c "
from apps.accounts.models import User, Teacher, Student, Group
from apps.courses.models import Lessons, Attendance
from apps.assignments.models import Homework, Task
from apps.submissions.models import HomeworkSubmission, TestCase
from apps.progress.models import HomeworkProgress, TaskProgress

print(f'👥 Users: {User.objects.count()}')
print(f'👨‍🏫 Teachers: {Teacher.objects.count()}')
print(f'👨‍🎓 Students: {Student.objects.count()}')
print(f'👥 Groups: {Group.objects.count()}')
print(f'📚 Lessons: {Lessons.objects.count()}')
print(f'📋 Attendance: {Attendance.objects.count()}')
print(f'📝 Homework: {Homework.objects.count()}')
print(f'📋 Tasks: {Task.objects.count()}')
print(f'💾 Submissions: {HomeworkSubmission.objects.count()}')
print(f'🧪 Test Cases: {TestCase.objects.count()}')
print(f'📊 Homework Progress: {HomeworkProgress.objects.count()}')
print(f'📈 Task Progress: {TaskProgress.objects.count()}')
"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Run './dummy_data.sh help' for available commands"
        exit 1
        ;;
esac

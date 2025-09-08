# Dummy Data Management Commands

This document describes the management commands available for creating and managing dummy data in the CodeSchool backend application.

## Quick Start

To create all dummy data with default values:

```bash
python manage.py create_all_dummy_data
```

To clean all dummy data:

```bash
python manage.py clean_all_dummy_data --confirm
```

## Individual App Commands

### 1. Accounts App (`create_accounts_dummy_data`)

Creates users, teachers, students, and groups.

```bash
python manage.py create_accounts_dummy_data --teachers 10 --students 50 --groups 5
```

**What it creates:**
- User accounts for teachers and students
- Teacher profiles with contact information
- Student profiles with parent contact information
- Groups with teacher assignments
- Student-group relationships

### 2. Courses App (`create_courses_dummy_data`)

Creates lessons and attendance records.

```bash
python manage.py create_courses_dummy_data --lessons 20 --attendance-records 100
```

**What it creates:**
- Lessons with titles, descriptions, and content
- Teacher-lesson assignments
- Attendance records linking students, lessons, groups, and teachers
- Various attendance statuses (present, absent, late, excused)

**Dependencies:** Requires accounts data to exist first.

### 3. Assignments App (`create_assignments_dummy_data`)

Creates homework assignments and tasks.

```bash
python manage.py create_assignments_dummy_data --homework 30 --tasks 100
```

**What it creates:**
- Homework assignments linked to lessons
- Tasks within homework assignments
- Varied task types (programming, math, general)

**Dependencies:** Requires courses data to exist first.

### 4. Submissions App (`create_submissions_dummy_data`)

Creates student submissions and test cases.

```bash
python manage.py create_submissions_dummy_data --submissions 200 --test-cases 150
```

**What it creates:**
- Student code submissions for tasks
- Test cases for automatic grading
- Execution results and performance metrics
- Multiple submission attempts per student

**Dependencies:** Requires assignments and accounts data to exist first.

### 5. Progress App (`create_progress_dummy_data`)

Creates progress tracking records.

```bash
python manage.py create_progress_dummy_data --homework-progress 100 --task-progress 300
```

**What it creates:**
- Homework completion progress per student
- Individual task progress tracking
- Completion percentages and timestamps
- Links to latest submissions

**Dependencies:** Requires all other apps' data to exist first.

## Master Command: `create_all_dummy_data`

This command runs all individual commands in the correct dependency order.

```bash
python manage.py create_all_dummy_data [options]
```

### Available Options:

- `--teachers N`: Number of teachers to create (default: 10)
- `--students N`: Number of students to create (default: 50)
- `--groups N`: Number of groups to create (default: 5)
- `--lessons N`: Number of lessons to create (default: 20)
- `--attendance-records N`: Number of attendance records (default: 100)
- `--homework N`: Number of homework assignments (default: 30)
- `--tasks N`: Number of tasks to create (default: 100)
- `--submissions N`: Number of submissions to create (default: 200)
- `--test-cases N`: Number of test cases to create (default: 150)
- `--homework-progress N`: Number of homework progress records (default: 100)
- `--task-progress N`: Number of task progress records (default: 300)

### Skip Options:

- `--skip-accounts`: Skip creating accounts data
- `--skip-courses`: Skip creating courses data
- `--skip-assignments`: Skip creating assignments data
- `--skip-submissions`: Skip creating submissions data
- `--skip-progress`: Skip creating progress data

### Examples:

Create a small dataset for testing:
```bash
python manage.py create_all_dummy_data --teachers 3 --students 15 --groups 2 --lessons 10
```

Create only accounts and courses:
```bash
python manage.py create_all_dummy_data --skip-assignments --skip-submissions --skip-progress
```

## Cleanup Command: `clean_all_dummy_data`

Removes all dummy data from the database.

```bash
python manage.py clean_all_dummy_data --confirm
```

### Options:

- `--confirm`: Required flag to confirm deletion
- `--keep-superusers`: Preserve superuser accounts during cleanup

### Example:

Clean all data but keep admin accounts:
```bash
python manage.py clean_all_dummy_data --confirm --keep-superusers
```

## Data Relationships

The dummy data maintains proper relationships between models:

1. **Users** → **Teachers/Students** (one-to-one)
2. **Groups** ↔ **Teachers** (many-to-many)
3. **Groups** ↔ **Students** (many-to-many)
4. **Lessons** ↔ **Teachers** (many-to-many)
5. **Homework** → **Lessons** (foreign key)
6. **Tasks** → **Homework** (foreign key)
7. **Attendance** → Student/Lesson/Group/Teacher (foreign keys)
8. **Submissions** → Task/Student (foreign keys)
9. **Progress** → Homework/Task/Student (foreign keys)

## Generated Data Characteristics

### Realistic Data:
- Names, emails, and phone numbers using Faker library
- Varied subjects (Math, Physics, Computer Science, etc.)
- Different task types (programming, math problems, essays)
- Realistic code submissions with syntax
- Various attendance patterns

### Educational Context:
- Programming tasks with sample code
- Test cases for automatic grading
- Progress tracking with completion percentages
- Multiple submission attempts per student
- Homework assignments with multiple tasks

## Requirements

The commands require the `faker` library, which is automatically installed when running the commands for the first time.

## Troubleshooting

### Common Issues:

1. **Missing Dependencies**: Run commands in order or use `create_all_dummy_data`
2. **Duplicate Data**: Commands check for existing records to avoid conflicts
3. **Database Errors**: Use `--confirm` flag carefully with cleanup command
4. **Performance**: Large datasets may take several minutes to create

### Database Reset:

To completely reset your database:
```bash
python manage.py clean_all_dummy_data --confirm
python manage.py migrate
python manage.py create_all_dummy_data
```

## Development Notes

- All commands use database transactions for safety
- Faker library generates realistic but fake data
- Commands include progress indicators and success messages
- Error handling with rollback on failures
- Configurable data sizes for different testing needs

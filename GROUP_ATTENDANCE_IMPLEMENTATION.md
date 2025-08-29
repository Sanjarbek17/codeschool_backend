# Group and Attendance Models Implementation

## Overview
Successfully implemented Group and Attendance models for the CodeSchool backend project, allowing teachers to manage groups and track student attendance for specific lessons.

## Models Created

### 1. Group Model (`apps/accounts/models.py`)
- **Fields:**
  - `name`: Unique group name
  - `created_date`: Timestamp when group was created
  - `teachers`: Many-to-many relationship with Teacher model
  - `updated_at`: Timestamp for last update

- **Relationships:**
  - Many-to-many with `Teacher` (teachers can teach multiple groups)
  - Many-to-many with `Student` (students can attend multiple groups)

- **Methods:**
  - `teacher_count`: Returns number of teachers assigned
  - `student_count`: Returns number of students enrolled

### 2. Updated Student Model (`apps/accounts/models.py`)
- **New Field:**
  - `groups`: Many-to-many relationship with Group model

### 3. Attendance Model (`apps/courses/models.py`)
- **Fields:**
  - `student`: Foreign key to Student
  - `lesson`: Foreign key to Lessons
  - `group`: Foreign key to Group
  - `teacher`: Foreign key to Teacher (who recorded attendance)
  - `status`: Choice field (present, absent, late, excused)
  - `date`: Date of the lesson
  - `notes`: Optional notes about attendance

- **Validation:**
  - Ensures student belongs to the group
  - Ensures teacher is assigned to the group
  - Unique constraint on student, lesson, group, and date

- **Methods:**
  - `is_present`: Returns True if student was present or late

## API Endpoints

### Group Management
- `GET /accounts/groups/` - List all groups
- `POST /accounts/groups/` - Create new group
- `GET /accounts/groups/{id}/` - Get group details
- `PUT/PATCH /accounts/groups/{id}/` - Update group
- `DELETE /accounts/groups/{id}/` - Delete group

### Attendance Management
- `GET /courses/attendance/` - List attendance records
- `POST /courses/attendance/` - Create attendance record
- `GET /courses/attendance/{id}/` - Get attendance details
- `PUT/PATCH /courses/attendance/{id}/` - Update attendance
- `DELETE /courses/attendance/{id}/` - Delete attendance record

### Custom Attendance Endpoints
- `GET /courses/attendance/by_group/?group_id={id}&date={date}` - Get attendance by group and date
- `GET /courses/attendance/by_student/?student_id={id}` - Get attendance for specific student
- `POST /courses/attendance/bulk_create/` - Create multiple attendance records at once

## Serializers

### Group Serializers
- `GroupSerializer` - Full group details with teachers and students
- `GroupListSerializer` - Simplified for list views
- `GroupCreateUpdateSerializer` - For creating/updating groups

### Attendance Serializers
- `AttendanceSerializer` - Full attendance details
- `AttendanceListSerializer` - Simplified for list views
- `AttendanceCreateUpdateSerializer` - For creating/updating attendance

## Admin Interface
- Added admin configurations for both Group and Attendance models
- Group admin includes teacher and student counts
- Attendance admin with filtering by date, status, group, and teacher
- Optimized querysets with select_related and prefetch_related

## Permissions & Security
- Teachers can only view/edit attendance for their assigned groups
- Students can only view their own attendance records
- Validation ensures data integrity between relationships

## Database Migrations
- `accounts/0002_group_student_groups.py` - Creates Group model and adds groups field to Student
- `courses/0002_attendance.py` - Creates Attendance model

## Testing
Created comprehensive test script (`test_models.py`) that validates:
- Model creation and relationships
- Data integrity constraints
- Validation rules
- Many-to-many relationships

## Usage Examples

### Creating a Group
```python
from apps.accounts.models import Teacher, Group

# Create group and assign teachers
group = Group.objects.create(name="Python Programming 101")
group.teachers.add(teacher1, teacher2)
```

### Enrolling Students
```python
from apps.accounts.models import Student

student = Student.objects.get(id=1)
student.groups.add(group)
```

### Recording Attendance
```python
from apps.courses.models import Attendance

attendance = Attendance.objects.create(
    student=student,
    lesson=lesson,
    group=group,
    teacher=teacher,
    status='present',
    date=date.today(),
    notes='Student was engaged and active'
)
```

## Key Features Implemented

1. **Multi-teacher Groups**: Teachers can collaborate on teaching the same group
2. **Multi-group Students**: Students can attend multiple groups simultaneously  
3. **Attendance Tracking**: Comprehensive attendance system with multiple status options
4. **Data Validation**: Ensures students can only have attendance recorded for groups they're enrolled in
5. **Flexible API**: RESTful API with filtering and bulk operations
6. **Admin Interface**: User-friendly admin interface for managing groups and attendance
7. **Permission System**: Role-based access control for teachers and students

The implementation follows Django best practices and provides a robust foundation for managing educational groups and attendance tracking.

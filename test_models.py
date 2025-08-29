#!/usr/bin/env python
"""
Test script to demonstrate Group and Attendance models functionality.
This script creates sample data to test the relationships between
Teacher, Student, Group, Lesson, and Attendance models.
"""

import os
import sys
import django
from datetime import date, datetime

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Teacher, Student, Group
from apps.courses.models import Lessons, Attendance

User = get_user_model()


def create_sample_data():
    """Create sample data to test the models."""
    print("Creating sample data...")

    # Create users
    teacher_user = User.objects.create_user(
        username="teacher1", email="teacher1@example.com", password="testpass123"
    )

    student_user = User.objects.create_user(
        username="student1", email="student1@example.com", password="testpass123"
    )

    # Create teacher profile
    teacher = Teacher.objects.create(
        user=teacher_user,
        first_name="John",
        last_name="Doe",
        phone_number="+1234567890",
    )
    print(f"Created teacher: {teacher}")

    # Create student profile
    student = Student.objects.create(
        user=student_user,
        first_name="Jane",
        last_name="Smith",
        phone_number="+1234567891",
        parents_phone_number="+1234567892",
    )
    print(f"Created student: {student}")

    # Create group
    group = Group.objects.create(name="Python Programming 101")
    group.teachers.add(teacher)
    student.groups.add(group)
    print(f"Created group: {group}")
    print(
        f"Group has {group.teacher_count} teachers and {group.student_count} students"
    )

    # Create lesson
    lesson = Lessons.objects.create(
        title="Introduction to Python",
        description="Basic Python programming concepts",
        content="Variables, data types, control structures",
    )
    lesson.teachers.add(teacher)
    print(f"Created lesson: {lesson}")

    # Create attendance record
    attendance = Attendance.objects.create(
        student=student,
        lesson=lesson,
        group=group,
        teacher=teacher,
        status="present",
        date=date.today(),
        notes="Student was active and engaged",
    )
    print(f"Created attendance: {attendance}")
    print(f"Student is present: {attendance.is_present}")

    return {
        "teacher": teacher,
        "student": student,
        "group": group,
        "lesson": lesson,
        "attendance": attendance,
    }


def test_relationships():
    """Test model relationships."""
    print("\n" + "=" * 50)
    print("Testing Model Relationships")
    print("=" * 50)

    # Get the data
    teacher = Teacher.objects.get(first_name="John")
    student = Student.objects.get(first_name="Jane")
    group = Group.objects.get(name="Python Programming 101")
    lesson = Lessons.objects.get(title="Introduction to Python")

    # Test teacher -> groups relationship
    print(f"\nTeacher {teacher.full_name} teaches {teacher.groups.count()} groups:")
    for g in teacher.groups.all():
        print(f"  - {g.name}")

    # Test student -> groups relationship
    print(f"\nStudent {student.full_name} attends {student.groups.count()} groups:")
    for g in student.groups.all():
        print(f"  - {g.name}")

    # Test group -> teachers and students relationship
    print(f"\nGroup '{group.name}' has:")
    print(f"  Teachers ({group.teacher_count}):")
    for t in group.teachers.all():
        print(f"    - {t.full_name}")
    print(f"  Students ({group.student_count}):")
    for s in group.students.all():
        print(f"    - {s.full_name}")

    # Test attendance records
    print(f"\nAttendance records for {student.full_name}:")
    for att in student.attendances.all():
        print(f"  - {att.lesson.title}: {att.get_status_display()} on {att.date}")

    print(f"\nAttendance records recorded by {teacher.full_name}:")
    for att in teacher.recorded_attendances.all():
        print(
            f"  - {att.student.full_name} in {att.lesson.title}: {att.get_status_display()}"
        )


def test_validation():
    """Test model validation."""
    print("\n" + "=" * 50)
    print("Testing Model Validation")
    print("=" * 50)

    teacher = Teacher.objects.get(first_name="John")
    student = Student.objects.get(first_name="Jane")
    group = Group.objects.get(name="Python Programming 101")
    lesson = Lessons.objects.get(title="Introduction to Python")

    # Try to create attendance for student not in group
    try:
        # Create a new group that student doesn't belong to
        other_group = Group.objects.create(name="Advanced Python")
        other_group.teachers.add(teacher)

        attendance = Attendance(
            student=student,
            lesson=lesson,
            group=other_group,  # Student is not in this group
            teacher=teacher,
            status="present",
            date=date.today(),
        )
        attendance.save()
        print("ERROR: Should have failed - student not in group")
    except ValueError as e:
        print(f"✓ Validation working: {e}")

    # Try to create attendance with teacher not assigned to group
    try:
        # Create another teacher
        other_teacher_user = User.objects.create_user(
            username="teacher2", email="teacher2@example.com", password="testpass123"
        )
        other_teacher = Teacher.objects.create(
            user=other_teacher_user,
            first_name="Bob",
            last_name="Wilson",
            phone_number="+1234567893",
        )

        attendance = Attendance(
            student=student,
            lesson=lesson,
            group=group,
            teacher=other_teacher,  # Teacher not assigned to group
            status="present",
            date=date.today(),
        )
        attendance.save()
        print("ERROR: Should have failed - teacher not assigned to group")
    except ValueError as e:
        print(f"✓ Validation working: {e}")


def main():
    """Main function to run all tests."""
    print("Group and Attendance Models Test")
    print("=" * 50)

    # Clean up existing data
    Attendance.objects.all().delete()
    Lessons.objects.all().delete()
    Group.objects.all().delete()
    Student.objects.all().delete()
    Teacher.objects.all().delete()
    User.objects.filter(username__startswith="teacher").delete()
    User.objects.filter(username__startswith="student").delete()

    # Create and test sample data
    create_sample_data()
    test_relationships()
    test_validation()

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()

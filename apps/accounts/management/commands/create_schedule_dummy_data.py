from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from apps.accounts.models import Teacher, Group, Schedule
from faker import Faker
from datetime import datetime, time, date, timedelta
import random

fake = Faker()


class Command(BaseCommand):
    help = "Create dummy data for Schedule models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--schedules", type=int, default=30, help="Number of schedules to create"
        )

    def handle(self, *args, **options):
        schedules_count = options["schedules"]

        self.stdout.write("Creating dummy data for Schedule models...")

        # Get existing teachers and groups
        teachers = list(Teacher.objects.all())
        groups = list(Group.objects.all())

        if not teachers:
            self.stdout.write(
                self.style.WARNING(
                    "No teachers found. Run create_accounts_dummy_data first."
                )
            )
            return

        if not groups:
            self.stdout.write(
                self.style.WARNING(
                    "No groups found. Run create_accounts_dummy_data first."
                )
            )
            return

        # Days of the week
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        # Common lesson times
        time_slots = [
            (time(8, 0), time(9, 30)),  # 8:00 - 9:30
            (time(9, 45), time(11, 15)),  # 9:45 - 11:15
            (time(11, 30), time(13, 0)),  # 11:30 - 13:00
            (time(14, 0), time(15, 30)),  # 14:00 - 15:30
            (time(15, 45), time(17, 15)),  # 15:45 - 17:15
            (time(17, 30), time(19, 0)),  # 17:30 - 19:00
            (time(19, 15), time(20, 45)),  # 19:15 - 20:45
        ]

        # Create schedules
        self.stdout.write(f"Creating {schedules_count} schedules...")
        created_schedules = []

        for i in range(schedules_count):
            # Choose random teacher and group
            teacher = random.choice(teachers)
            group = random.choice(groups)

            # Ensure teacher is assigned to the group
            if teacher not in group.teachers.all():
                group.teachers.add(teacher)

            # Choose random day and time slot
            day = random.choice(days)
            start_time, end_time = random.choice(time_slots)

            # Generate start date (between 1 month ago and 3 months from now)
            today = date.today()
            start_date = fake.date_between(
                start_date=today - timedelta(days=30),
                end_date=today + timedelta(days=90),
            )

            # Check if similar schedule already exists to avoid duplicates
            existing_schedule = Schedule.objects.filter(
                group=group, teacher=teacher, day_of_week=day, start_time=start_time
            ).first()

            if existing_schedule:
                continue  # Skip if similar schedule exists

            try:
                schedule = Schedule.objects.create(
                    group=group,
                    teacher=teacher,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time,
                    start_date=start_date,
                    end_date=(
                        None
                        if random.choice([True, False])
                        else fake.date_between(
                            start_date=start_date + timedelta(weeks=4),
                            end_date=start_date + timedelta(weeks=20),
                        )
                    ),
                    is_recurring=True,
                    is_active=random.choice([True, True, True, False]),  # 75% active
                )

                created_schedules.append(schedule)

            except ValidationError as e:
                self.stdout.write(
                    self.style.WARNING(f"Validation error creating schedule: {e}")
                )
                continue
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error creating schedule: {e}"))
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(created_schedules)} schedules"
            )
        )

        # Show sample of created schedules
        for schedule in created_schedules[:5]:
            self.stdout.write(
                f"  - {schedule.teacher.full_name} teaches {schedule.group.name} "
                f"every {schedule.day_of_week} ({schedule.start_time}-{schedule.end_time})"
            )

        if len(created_schedules) > 5:
            self.stdout.write(f"  ... and {len(created_schedules) - 5} more schedules")

        # Show statistics by day
        self.stdout.write("\nSchedules by day:")
        for day in days:
            count = len([s for s in created_schedules if s.day_of_week == day])
            if count > 0:
                self.stdout.write(f"  {day}: {count} schedules")

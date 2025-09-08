"""
Management command to run automated tests on existing submissions.

This command allows administrators and teachers to:
1. Re-test all submissions for better accuracy
2. Test submissions that were created before automated testing was implemented
3. Re-evaluate submissions after test cases have been updated
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from apps.submissions.models import HomeworkSubmission, TestCase
from apps.editor.services import AutomatedTestRunner
import time


class Command(BaseCommand):
    help = "Run automated tests on existing homework submissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task-id",
            type=int,
            help="Test submissions for a specific task ID only",
        )
        parser.add_argument(
            "--student-id",
            type=int,
            help="Test submissions for a specific student ID only",
        )
        parser.add_argument(
            "--submission-id",
            type=int,
            help="Test a specific submission ID only",
        )
        parser.add_argument(
            "--retest-all",
            action="store_true",
            help="Re-test all submissions, including those already tested",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be tested without actually running tests",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of submissions to process in each batch (default: 10)",
        )

    def handle(self, *args, **options):
        """Main command handler."""

        self.stdout.write(
            self.style.SUCCESS("🧪 Automated Testing Command for Homework Submissions")
        )
        self.stdout.write("=" * 60)

        # Build queryset based on options
        queryset = HomeworkSubmission.objects.all()

        if options["task_id"]:
            queryset = queryset.filter(task_id=options["task_id"])
            self.stdout.write(f"📋 Filtering by task ID: {options['task_id']}")

        if options["student_id"]:
            queryset = queryset.filter(student_id=options["student_id"])
            self.stdout.write(f"👨‍🎓 Filtering by student ID: {options['student_id']}")

        if options["submission_id"]:
            queryset = queryset.filter(id=options["submission_id"])
            self.stdout.write(
                f"📝 Testing specific submission ID: {options['submission_id']}"
            )

        # Filter submissions that have code to test
        queryset = (
            queryset.filter(Q(code_text__isnull=False) & ~Q(code_text=""))
            .select_related("task", "student__user")
            .order_by("id")
        )

        if not options["retest_all"]:
            # Only test submissions that haven't been tested yet (passed_tests = 0)
            queryset = queryset.filter(passed_tests=0)
            self.stdout.write(
                "📊 Only testing submissions that haven't been tested yet"
            )
        else:
            self.stdout.write(
                "🔄 Re-testing all submissions (including previously tested)"
            )

        total_submissions = queryset.count()

        if total_submissions == 0:
            self.stdout.write(
                self.style.WARNING("⚠️  No submissions found matching the criteria.")
            )
            return

        self.stdout.write(f"📊 Found {total_submissions} submissions to process")

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(
                    "🔍 DRY RUN MODE - No actual testing will be performed"
                )
            )
            self._show_dry_run_info(queryset)
            return

        # Confirm before proceeding
        if total_submissions > 20:
            confirm = input(
                f"Are you sure you want to test {total_submissions} submissions? (y/N): "
            )
            if confirm.lower() != "y":
                self.stdout.write("❌ Operation cancelled")
                return

        # Initialize test runner
        test_runner = AutomatedTestRunner()

        # Process submissions in batches
        batch_size = options["batch_size"]
        processed = 0
        successful = 0
        failed = 0
        start_time = time.time()

        self.stdout.write(f"🚀 Starting automated testing (batch size: {batch_size})")
        self.stdout.write("")

        for i in range(0, total_submissions, batch_size):
            batch = queryset[i : i + batch_size]

            self.stdout.write(
                f"📦 Processing batch {i//batch_size + 1} ({len(batch)} submissions)"
            )

            for submission in batch:
                try:
                    # Check if task has test cases
                    test_case_count = TestCase.objects.filter(
                        task=submission.task
                    ).count()

                    if test_case_count == 0:
                        self.stdout.write(
                            f"  ⚠️  Skipping submission {submission.id} - no test cases for task '{submission.task.title}'"
                        )
                        continue

                    # Store previous results
                    old_passed = submission.passed_tests
                    old_total = submission.total_tests

                    # Run automated tests
                    results = test_runner.evaluate_and_update_submission(submission)

                    # Report results
                    self.stdout.write(
                        f"  ✅ Submission {submission.id}: "
                        f"{submission.student.user.get_full_name()} - {submission.task.title}"
                    )
                    self.stdout.write(
                        f"     📊 Results: {results.passed_tests}/{results.total_tests} tests passed "
                        f"({results.success_rate:.1f}%)"
                    )

                    if (
                        old_passed != results.passed_tests
                        or old_total != results.total_tests
                    ):
                        self.stdout.write(
                            f"     🔄 Updated from: {old_passed}/{old_total} to: "
                            f"{results.passed_tests}/{results.total_tests}"
                        )

                    successful += 1

                except Exception as e:
                    self.stdout.write(
                        f"  ❌ Failed to test submission {submission.id}: {str(e)}"
                    )
                    failed += 1

                processed += 1

                # Show progress
                if processed % 5 == 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = (
                        (total_submissions - processed) / rate if rate > 0 else 0
                    )

                    self.stdout.write(
                        f"  📈 Progress: {processed}/{total_submissions} "
                        f"({processed/total_submissions*100:.1f}%) - "
                        f"ETA: {remaining:.0f}s"
                    )

            self.stdout.write("")  # Empty line between batches

        # Final summary
        elapsed_time = time.time() - start_time

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("🎉 Automated Testing Complete!"))
        self.stdout.write("")
        self.stdout.write(f"📊 Total processed: {processed}")
        self.stdout.write(f"✅ Successful: {successful}")
        self.stdout.write(f"❌ Failed: {failed}")
        self.stdout.write(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        self.stdout.write(
            f"🚀 Average rate: {processed/elapsed_time:.2f} submissions/second"
        )

        if failed > 0:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {failed} submissions failed to process. "
                    "Check the error messages above for details."
                )
            )

    def _show_dry_run_info(self, queryset):
        """Show information about what would be tested in dry run mode."""

        self.stdout.write("")
        self.stdout.write("📋 Dry Run Summary:")
        self.stdout.write("-" * 40)

        # Group by task
        task_counts = {}
        for submission in queryset:
            task_title = submission.task.title
            if task_title not in task_counts:
                task_counts[task_title] = 0
            task_counts[task_title] += 1

        for task_title, count in task_counts.items():
            self.stdout.write(f"  📝 {task_title}: {count} submissions")

        # Show sample submissions
        self.stdout.write("")
        self.stdout.write("📋 Sample submissions that would be tested:")
        self.stdout.write("-" * 40)

        for submission in queryset[:10]:  # Show first 10
            test_case_count = TestCase.objects.filter(task=submission.task).count()
            self.stdout.write(
                f"  ID {submission.id}: {submission.student.user.get_full_name()} - "
                f"{submission.task.title} ({test_case_count} test cases)"
            )

        if queryset.count() > 10:
            self.stdout.write(f"  ... and {queryset.count() - 10} more")

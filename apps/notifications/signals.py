from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

# Import models from other apps
from apps.assignments.models import Homework
from apps.submissions.models import HomeworkSubmission
from apps.progress.models import HomeworkProgress
from apps.accounts.models import Student, Teacher, Group
from apps.admin_panel.models import Payment

# Import notification utilities
from .utils import (
    create_notification,
    create_bulk_notifications,
    create_payment_notification,
)
from .models import Notification

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Homework)
def notify_new_homework(sender, instance, created, **kwargs):
    """
    Notify teachers when new homework is created.
    This is a teacher-only notification.
    """
    if created:
        # Get all teachers from groups related to this homework's lesson
        lesson = instance.lesson
        if lesson and lesson.course:
            # Get all groups currently teaching this course
            groups = Group.objects.filter(current_course=lesson.course)

            # Get all teachers from these groups
            teacher_ids = set()
            for group in groups:
                teacher_ids.update(group.teachers.values_list("user_id", flat=True))

            # Get teacher user objects
            teachers = User.objects.filter(id__in=teacher_ids)

            # Create notifications for teachers
            for teacher in teachers:
                create_notification(
                    title=f"New Homework: {instance.title}",
                    message=f"New homework has been created for {lesson.title}: {instance.description}",
                    notification_type="assignment",
                    recipient_role="teacher",
                    recipient=teacher,
                    priority="medium",
                    related_object=instance,
                )


@receiver(post_save, sender=HomeworkSubmission)
def notify_homework_submission(sender, instance, created, **kwargs):
    """
    Notify teachers when students submit homework.
    This is a teacher-only notification.
    """
    if created:
        # Get the student's groups
        student_groups = instance.student.groups.all()

        # Get all teachers from these groups
        teacher_ids = set()
        for group in student_groups:
            teacher_ids.update(group.teachers.values_list("user_id", flat=True))

        # Get teacher user objects
        teachers = User.objects.filter(id__in=teacher_ids)

        # Create notifications for teachers
        for teacher in teachers:
            create_notification(
                title=f"New Submission: {instance.task.title}",
                message=f"{instance.student.full_name} has submitted homework for {instance.task.title}. "
                f"Tests passed: {instance.passed_tests}/{instance.total_tests}",
                notification_type="submission",
                recipient_role="teacher",
                recipient=teacher,
                priority="medium",
                related_object=instance,
            )
    else:
        # If submission was updated (e.g., graded), notify the student
        # But students are not included in our system, so we notify teachers about grading completion
        if hasattr(instance, "_state") and instance._state.adding is False:
            # Get the student's groups
            student_groups = instance.student.groups.all()

            # Get all teachers from these groups
            teacher_ids = set()
            for group in student_groups:
                teacher_ids.update(group.teachers.values_list("user_id", flat=True))

            # Get teacher user objects
            teachers = User.objects.filter(id__in=teacher_ids)

            # Create notifications for teachers about grading update
            for teacher in teachers:
                create_notification(
                    title=f"Submission Updated: {instance.task.title}",
                    message=f"Submission by {instance.student.full_name} has been updated. "
                    f"Tests passed: {instance.passed_tests}/{instance.total_tests}",
                    notification_type="submission",
                    recipient_role="teacher",
                    recipient=teacher,
                    priority="low",
                    related_object=instance,
                )


@receiver(post_save, sender=HomeworkProgress)
def notify_homework_progress(sender, instance, created, **kwargs):
    """
    Notify teachers when students make progress on homework.
    This is a teacher-only notification.
    """
    if created or instance.is_completed:
        # Get the student's groups
        student_groups = instance.student.groups.all()

        # Get all teachers from these groups
        teacher_ids = set()
        for group in student_groups:
            teacher_ids.update(group.teachers.values_list("user_id", flat=True))

        # Get teacher user objects
        teachers = User.objects.filter(id__in=teacher_ids)

        # Determine message based on completion
        if instance.is_completed:
            title = f"Homework Completed: {instance.homework.title}"
            message = f"{instance.student.full_name} has completed homework: {instance.homework.title}"
            priority = "medium"
        else:
            title = f"Progress Update: {instance.homework.title}"
            message = f"{instance.student.full_name} made progress on {instance.homework.title}: "
            message += f"{instance.solved_tasks}/{instance.total_tasks} tasks completed"
            priority = "low"

        # Create notifications for teachers
        for teacher in teachers:
            create_notification(
                title=title,
                message=message,
                notification_type="progress",
                recipient_role="teacher",
                recipient=teacher,
                priority=priority,
                related_object=instance,
            )


@receiver(post_save, sender=Group)
def notify_group_changes(sender, instance, created, **kwargs):
    """
    Notify teachers when groups are created or modified.
    This is a teacher-only notification.
    """
    if created:
        # Get all admin users to notify about new group
        admin_users = User.objects.filter(is_staff=True, is_superuser=True)

        # Create notifications for admins
        for admin in admin_users:
            create_notification(
                title=f"New Group Created: {instance.name}",
                message=f"A new group '{instance.name}' has been created.",
                notification_type="announcement",
                recipient_role="admin",
                recipient=admin,
                priority="low",
                related_object=instance,
            )


# Signal to create sample payment notifications (this would be replaced with actual payment system integration)
def create_sample_payment_notifications():
    """
    This function demonstrates how payment notifications would be created.
    In a real system, this would be triggered by payment gateway webhooks or payment processing.
    """
    # This is just an example - in reality, payment notifications would be triggered by:
    # - Payment gateway webhooks
    # - Scheduled tasks checking for overdue payments
    # - Manual payment processing by admin

    # Example: Student payment overdue
    from .utils import create_payment_notification
    from apps.accounts.models import Student

    # Get a sample student (this would come from actual payment data)
    try:
        sample_student = Student.objects.first()
        if sample_student:
            create_payment_notification(
                title="Overdue Payment Alert",
                message=f"Student {sample_student.full_name} has an overdue tuition payment.",
                payment_type="tuition",
                payment_status="overdue",
                amount=500.00,
                currency="USD",
                student=sample_student,
                payment_reference=f"TUI-{sample_student.id}-{timezone.now().strftime('%Y%m%d')}",
            )
    except Exception as e:
        pass  # In production, you'd log this error


# Real Payment signal handlers for automatic notifications


@receiver(post_save, sender=Payment)
def handle_payment_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal triggered when Payment is created or updated
    Automatically checks and sends notifications based on payment status
    """
    try:
        if created:
            # New payment created - check if it needs immediate attention
            logger.info(f"New payment created for {instance.student.get_full_name()}")

            # Check if payment is due soon (within 3 days)
            days_until_due = (instance.due_date - timezone.now().date()).days

            if 0 <= days_until_due <= 3:
                # Get student profile
                student_profile = getattr(instance.student, "student_profile", None)
                if student_profile:
                    create_payment_notification(
                        title=f"Payment Due Soon: {instance.student.get_full_name()}",
                        message=f"Payment for {instance.student.get_full_name()} in {instance.group.name} "
                        f"is due on {instance.due_date}. "
                        f"Amount: ${instance.remaining_amount} (Period: {instance.payment_period})",
                        payment_type="tuition",
                        payment_status=instance.status,
                        amount=float(instance.remaining_amount),
                        due_date=instance.due_date,
                        student=student_profile,
                        payment_reference=f"TUI-{instance.student.id}-{instance.id}",
                    )
                logger.info(f"Sent due soon notification for payment {instance.id}")

        else:
            # Payment updated - check for status changes
            logger.info(f"Payment updated for {instance.student.get_full_name()}")

            # Check if payment became overdue
            if instance.is_overdue and instance.status in ["pending", "partially_paid"]:
                student_profile = getattr(instance.student, "student_profile", None)
                if student_profile:
                    create_payment_notification(
                        title=f"Payment Overdue: {instance.student.get_full_name()}",
                        message=f"Payment for {instance.student.get_full_name()} in {instance.group.name} "
                        f"is {instance.days_overdue} days overdue! "
                        f"Due date: {instance.due_date}. "
                        f"Remaining amount: ${instance.remaining_amount}",
                        payment_type="tuition",
                        payment_status="overdue",
                        amount=float(instance.remaining_amount),
                        due_date=instance.due_date,
                        student=student_profile,
                        payment_reference=f"TUI-{instance.student.id}-{instance.id}",
                    )
                logger.info(f"Sent overdue notification for payment {instance.id}")

            # Check if payment was completed
            elif instance.is_fully_paid and instance.status == "paid":
                student_profile = getattr(instance.student, "student_profile", None)
                if student_profile:
                    create_payment_notification(
                        title=f"Payment Received: {instance.student.get_full_name()}",
                        message=f"Payment of ${instance.paid_amount} received from {instance.student.get_full_name()} "
                        f"for {instance.group.name} (Period: {instance.payment_period}). "
                        f"Payment is now complete.",
                        payment_type="tuition",
                        payment_status="paid",
                        amount=float(instance.paid_amount),
                        due_date=instance.due_date,
                        student=student_profile,
                        payment_reference=f"TUI-{instance.student.id}-{instance.id}",
                    )
                logger.info(
                    f"Sent payment received notification for payment {instance.id}"
                )

    except Exception as e:
        logger.error(f"Error in payment signal handler: {str(e)}")


@receiver(post_save, sender=Homework)
def check_student_payments_on_homework(sender, instance, created, **kwargs):
    """
    When new homework is created, check payment status of students in the group
    """
    if created and instance.lesson and instance.lesson.course:
        try:
            # Get groups teaching this course
            groups = Group.objects.filter(current_course=instance.lesson.course)

            for group in groups:
                trigger_group_payment_check(group)

        except Exception as e:
            logger.error(f"Error checking payments on homework creation: {str(e)}")


@receiver(post_save, sender=HomeworkSubmission)
def check_student_payment_on_submission(sender, instance, created, **kwargs):
    """
    When student submits homework, check their payment status
    """
    if created:
        try:
            trigger_student_payment_check(instance.student)
        except Exception as e:
            logger.error(f"Error checking payment on submission: {str(e)}")


# Helper functions for payment checks


def trigger_group_payment_check(group):
    """
    Check payment status for all students in a group
    """
    try:
        today = timezone.now().date()
        upcoming_due_date = today + timedelta(days=3)

        # Check for upcoming payments in this group
        upcoming_payments = Payment.objects.filter(
            group=group,
            due_date__lte=upcoming_due_date,
            status__in=["pending", "partially_paid"],
        ).select_related("student")

        for payment in upcoming_payments:
            days_until_due = (payment.due_date - today).days

            if days_until_due <= 3:
                student_profile = getattr(payment.student, "student_profile", None)
                if student_profile:
                    create_payment_notification(
                        title=f"Payment Reminder: {payment.student.get_full_name()}",
                        message=f"Student {payment.student.get_full_name()} in {group.name} "
                        f"has a payment due on {payment.due_date} "
                        f"(in {days_until_due} days). "
                        f"Remaining amount: ${payment.remaining_amount}",
                        payment_type="tuition",
                        payment_status=payment.status,
                        amount=float(payment.remaining_amount),
                        due_date=payment.due_date,
                        student=student_profile,
                        payment_reference=f"TUI-{payment.student.id}-{payment.id}",
                    )

        logger.info(f"Checked payment status for group {group.name}")

    except Exception as e:
        logger.error(f"Error checking group payment status: {str(e)}")


def trigger_student_payment_check(student):
    """
    Check payment status for a specific student
    """
    try:
        today = timezone.now().date()

        # Check for overdue payments
        overdue_payments = Payment.objects.filter(
            student=student,
            due_date__lt=today,
            status__in=["pending", "partially_paid"],
        ).select_related("group")

        for payment in overdue_payments:
            student_profile = getattr(student, "student_profile", None)
            if student_profile:
                create_payment_notification(
                    title=f"Overdue Payment: {student.get_full_name()}",
                    message=f"Student {student.get_full_name()} has an overdue payment "
                    f"for {payment.group.name}. "
                    f"Due date: {payment.due_date} "
                    f"({payment.days_overdue} days overdue). "
                    f"Remaining amount: ${payment.remaining_amount}",
                    payment_type="tuition",
                    payment_status="overdue",
                    amount=float(payment.remaining_amount),
                    due_date=payment.due_date,
                    student=student_profile,
                    payment_reference=f"TUI-{student.id}-{payment.id}",
                )

        # Check for upcoming payments (within 3 days)
        upcoming_payments = Payment.objects.filter(
            student=student,
            due_date__lte=today + timedelta(days=3),
            due_date__gte=today,
            status__in=["pending", "partially_paid"],
        ).select_related("group")

        for payment in upcoming_payments:
            days_until_due = (payment.due_date - today).days
            student_profile = getattr(student, "student_profile", None)
            if student_profile:
                create_payment_notification(
                    title=f"Payment Due Soon: {student.get_full_name()}",
                    message=f"Student {student.get_full_name()} has a payment due "
                    f"on {payment.due_date} (in {days_until_due} days) "
                    f"for {payment.group.name}. "
                    f"Remaining amount: ${payment.remaining_amount}",
                    payment_type="tuition",
                    payment_status=payment.status,
                    amount=float(payment.remaining_amount),
                    due_date=payment.due_date,
                    student=student_profile,
                    payment_reference=f"TUI-{student.id}-{payment.id}",
                )

        logger.info(f"Checked payment status for student {student.get_full_name()}")

    except Exception as e:
        logger.error(f"Error checking student payment status: {str(e)}")


# Manual trigger function for bulk payment checks
def trigger_bulk_payment_check():
    """
    Manual function to trigger payment checks for all students
    Can be called from views or management commands
    """
    try:
        today = timezone.now().date()

        # Check all payments due in next 3 days
        upcoming_payments = Payment.objects.filter(
            due_date__lte=today + timedelta(days=3),
            due_date__gte=today,
            status__in=["pending", "partially_paid"],
        ).select_related("student", "group")

        notifications_sent = 0

        for payment in upcoming_payments:
            days_until_due = (payment.due_date - today).days
            student_profile = getattr(payment.student, "student_profile", None)
            if student_profile:
                create_payment_notification(
                    title=f"Payment Due Alert: {payment.student.get_full_name()}",
                    message=f"Payment for {payment.student.get_full_name()} in {payment.group.name} "
                    f"is due on {payment.due_date} (in {days_until_due} days). "
                    f"Remaining amount: ${payment.remaining_amount}",
                    payment_type="tuition",
                    payment_status=payment.status,
                    amount=float(payment.remaining_amount),
                    due_date=payment.due_date,
                    student=student_profile,
                    payment_reference=f"TUI-{payment.student.id}-{payment.id}",
                )
                notifications_sent += 1

        # Check overdue payments
        overdue_payments = Payment.objects.filter(
            due_date__lt=today, status__in=["pending", "partially_paid"]
        ).select_related("student", "group")

        for payment in overdue_payments:
            student_profile = getattr(payment.student, "student_profile", None)
            if student_profile:
                create_payment_notification(
                    title=f"Overdue Payment Alert: {payment.student.get_full_name()}",
                    message=f"Payment for {payment.student.get_full_name()} in {payment.group.name} "
                    f"is overdue by {payment.days_overdue} days! "
                    f"Due date: {payment.due_date}. "
                    f"Remaining amount: ${payment.remaining_amount}",
                    payment_type="tuition",
                    payment_status="overdue",
                    amount=float(payment.remaining_amount),
                    due_date=payment.due_date,
                    student=student_profile,
                    payment_reference=f"TUI-{payment.student.id}-{payment.id}",
                )
                notifications_sent += 1

        logger.info(
            f"Bulk payment check completed. Sent {notifications_sent} notifications."
        )
        return notifications_sent

    except Exception as e:
        logger.error(f"Error in bulk payment check: {str(e)}")
        return 0

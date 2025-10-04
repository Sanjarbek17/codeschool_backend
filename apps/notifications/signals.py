from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Import models from other apps
from apps.assignments.models import Homework
from apps.submissions.models import HomeworkSubmission
from apps.progress.models import HomeworkProgress
from apps.accounts.models import Student, Teacher, Group

# Import notification utilities
from .utils import create_notification, create_bulk_notifications
from .models import Notification

User = get_user_model()


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


# Example signals for payment-related events (these would be connected to your payment models)
"""
@receiver(post_save, sender=Payment)  # Assuming you have a Payment model
def notify_payment_status(sender, instance, created, **kwargs):
    '''
    Notify admin when payment status changes.
    This is an admin-only notification.
    '''
    if not created:  # Only for updates
        from .utils import create_payment_notification
        
        title = f"Payment Status Update: {instance.payment_reference}"
        message = f"Payment {instance.payment_reference} status changed to {instance.status}"
        
        create_payment_notification(
            title=title,
            message=message,
            payment_type=instance.payment_type,
            payment_status=instance.status,
            amount=instance.amount,
            currency=instance.currency,
            student=instance.student if hasattr(instance, 'student') else None,
            teacher=instance.teacher if hasattr(instance, 'teacher') else None,
            payment_reference=instance.payment_reference
        )


@receiver(post_save, sender=StudentPayment)  # Assuming you have a StudentPayment model
def notify_student_payment(sender, instance, created, **kwargs):
    '''
    Notify admin about student payment events.
    This is an admin-only notification.
    '''
    if created:
        from .utils import create_payment_notification
        
        create_payment_notification(
            title=f"New Student Payment: {instance.student.full_name}",
            message=f"Student {instance.student.full_name} made a payment of {instance.amount} {instance.currency}",
            payment_type='tuition',
            payment_status=instance.status,
            amount=instance.amount,
            currency=instance.currency,
            student=instance.student,
            payment_reference=instance.reference
        )


@receiver(post_save, sender=TeacherSalary)  # Assuming you have a TeacherSalary model
def notify_teacher_salary(sender, instance, created, **kwargs):
    '''
    Notify admin about teacher salary payments.
    This is an admin-only notification.
    '''
    if created:
        from .utils import create_payment_notification
        
        create_payment_notification(
            title=f"Teacher Salary: {instance.teacher.full_name}",
            message=f"Salary payment processed for {instance.teacher.full_name}: {instance.amount} {instance.currency}",
            payment_type='salary',
            payment_status=instance.status,
            amount=instance.amount,
            currency=instance.currency,
            teacher=instance.teacher,
            payment_reference=instance.reference
        )
"""

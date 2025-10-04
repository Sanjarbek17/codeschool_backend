# Notification System Documentation

## Overview

The notification system provides a comprehensive solution for managing notifications in the CodeSchool backend with role-based filtering. The system supports different types of notifications including **payment notifications that are admin-only** and **teacher-specific notifications**.

## Key Features

### 🔐 Role-Based Access Control
- **Admin Users**: Can see all notifications including payment notifications
- **Teachers**: Can see assignment, submission, progress, and schedule notifications
- **Students**: Are excluded from the notification system (as per requirements)

### 💰 Payment Notifications (Admin Only)
- Student payment notifications
- Teacher salary notifications 
- Overdue payment alerts
- Payment status updates

### 📚 Teacher Notifications
- New homework assignments
- Student submissions
- Progress updates
- Schedule changes

## Models

### Notification
Main notification model with the following key fields:
- `title`: Notification title
- `message`: Notification content
- `notification_type`: Type from predefined choices
- `recipient_role`: Target role (admin, teacher, student, all)
- `recipient`: Specific user (optional)
- `priority`: Notification priority level
- `is_read`: Read status
- `related_object`: Generic foreign key to related model

### PaymentNotification
Specialized model for payment notifications (admin only):
- `payment_type`: tuition, salary, refund, penalty, bonus
- `payment_status`: pending, completed, failed, cancelled, overdue
- `amount`: Payment amount
- `currency`: Payment currency
- `student`/`teacher`: Related entities
- `payment_reference`: Unique payment reference

### NotificationPreference
User notification preferences with role-based settings:
- General preferences (email, push notifications)
- Teacher-specific preferences
- Admin-only payment notification preferences

## API Endpoints

### Notification Endpoints

#### List Notifications
```
GET /api/notifications/
```
**Access**: Teachers and Admin only
**Description**: Get paginated list of notifications based on user role

**Query Parameters**:
- `notification_type`: Filter by type
- `is_read`: Filter by read status
- `priority`: Filter by priority

#### Get Unread Notifications
```
GET /api/notifications/unread/
```
**Access**: Teachers and Admin only
**Description**: Get only unread notifications

#### Mark Notification as Read
```
POST /api/notifications/{id}/mark_read/
```
**Access**: Teachers and Admin only
**Description**: Mark a specific notification as read

#### Mark All Notifications as Read
```
POST /api/notifications/mark_all_read/
```
**Access**: Teachers and Admin only
**Body**:
```json
{
  "notification_ids": [1, 2, 3]  // Optional: specific IDs, empty for all
}
```

#### Get Notification Statistics
```
GET /api/notifications/stats/
```
**Access**: Teachers and Admin only
**Response**:
```json
{
  "total": 25,
  "unread": 5,
  "read": 20,
  "by_type": [...],
  "by_priority": [...]
}
```

#### Create Notification (Admin Only)
```
POST /api/notifications/create_notification/
```
**Access**: Admin only
**Body**:
```json
{
  "title": "New Announcement",
  "message": "Important announcement for all teachers",
  "notification_type": "announcement",
  "recipient_role": "teacher",
  "priority": "high"
}
```

### Payment Notification Endpoints (Admin Only)

#### List Payment Notifications
```
GET /api/payment-notifications/
```
**Access**: Admin only

#### Create Payment Notification
```
POST /api/payment-notifications/create_payment_notification/
```
**Access**: Admin only
**Body**:
```json
{
  "title": "Overdue Payment Alert",
  "message": "Student payment is overdue",
  "payment_type": "tuition",
  "payment_status": "overdue",
  "amount": "500.00",
  "currency": "USD",
  "student_id": 1,
  "due_date": "2025-10-01T00:00:00Z"
}
```

### Notification Preferences

#### Get User Preferences
```
GET /api/preferences/my_preferences/
```
**Access**: Authenticated users

#### Update User Preferences
```
PUT /api/preferences/update_preferences/
PATCH /api/preferences/update_preferences/
```
**Access**: Authenticated users
**Body**:
```json
{
  "email_notifications": true,
  "assignment_notifications": true,
  "payment_notifications": true  // Admin only
}
```

## Signal Triggers

The system automatically creates notifications based on model changes:

### Homework Signals
- **New Homework Created**: Notifies teachers in related groups
- **Homework Deadline**: Can be triggered via management command

### Submission Signals
- **New Submission**: Notifies teachers when students submit work
- **Submission Updated**: Notifies teachers when submissions are graded

### Progress Signals
- **Progress Updates**: Notifies teachers when students make progress
- **Homework Completed**: Notifies teachers when students complete homework

### Payment Signals (Example - for future integration)
```python
# Example payment signal (would be connected to your payment models)
@receiver(post_save, sender=Payment)
def notify_payment_status(sender, instance, created, **kwargs):
    if instance.status == 'overdue':
        create_payment_notification(
            title=f"Overdue Payment: {instance.student.full_name}",
            message=f"Payment is overdue by {instance.days_overdue} days",
            payment_type='tuition',
            payment_status='overdue',
            amount=instance.amount,
            student=instance.student
        )
```

## Management Commands

### Send Homework Reminders
```bash
python manage.py send_homework_reminders --days 1 --dry-run
```
**Purpose**: Send deadline reminders to teachers
**Options**:
- `--days`: Days ahead to check for deadlines (default: 1)
- `--dry-run`: Show what would be sent without sending

### Send Payment Reminders
```bash
python manage.py send_payment_reminders --type all --dry-run
```
**Purpose**: Send payment notifications to admin
**Options**:
- `--type`: tuition, salary, overdue, all
- `--dry-run`: Show what would be sent without sending

### Cleanup Old Notifications
```bash
python manage.py cleanup_notifications --days 30 --keep-payment --dry-run
```
**Purpose**: Clean up old read notifications
**Options**:
- `--days`: Delete notifications older than X days (default: 30)
- `--keep-payment`: Keep payment notifications even if old
- `--dry-run`: Show what would be deleted without deleting

## Authentication & Permissions

### Token Authentication
All notification endpoints require token authentication:
```bash
Authorization: Token YOUR_TOKEN_HERE
```

### Role-Based Permissions
- **IsTeacherOrAdmin**: Teacher and admin endpoints
- **IsAdminUser**: Admin-only endpoints (payment notifications)
- **IsAuthenticated**: User preference endpoints

### Role Detection
The system automatically detects user roles based on:
- `is_superuser` or `is_staff` → Admin
- Has `teacher_profile` → Teacher  
- Has `student_profile` → Student
- Default → Admin (for safety)

## Usage Examples

### Create a Teacher Notification
```python
from apps.notifications.utils import create_notification

notification = create_notification(
    title="New Assignment Available",
    message="A new coding assignment has been created for your group",
    notification_type='assignment',
    recipient_role='teacher',
    priority='medium'
)
```

### Create a Payment Notification (Admin Only)
```python
from apps.notifications.utils import create_payment_notification

payment_notification = create_payment_notification(
    title="Payment Overdue",
    message="Student John Doe has an overdue payment",
    payment_type='tuition',
    payment_status='overdue',
    amount=500.00,
    student=student_instance
)
```

### Get User Notifications
```python
from apps.notifications.utils import get_user_notifications

# Get all notifications for a teacher
notifications = get_user_notifications(teacher_user)

# Get only unread notifications
unread_notifications = get_user_notifications(teacher_user, unread_only=True)

# Get specific type of notifications
assignment_notifications = get_user_notifications(
    teacher_user, 
    notification_type='assignment'
)
```

## Database Indexes

The system includes optimized database indexes for:
- `recipient` + `is_read`
- `notification_type` + `recipient_role` 
- `created_at`

## Integration with Existing Models

The notification system integrates seamlessly with existing models:
- **Homework** → Assignment notifications
- **HomeworkSubmission** → Submission notifications
- **HomeworkProgress** → Progress notifications
- **Group** → Schedule change notifications

## Testing

Run the comprehensive test suite:
```bash
python manage.py test apps.notifications
```

The test suite covers:
- Model validation and constraints
- Role-based access control
- API endpoints functionality
- Signal triggers
- Utility functions
- Payment notification restrictions

## Security Considerations

1. **Payment Notifications**: Strictly limited to admin users
2. **Role Validation**: Automatic role detection and validation
3. **Data Isolation**: Users only see notifications for their role
4. **Input Validation**: Comprehensive validation in serializers and models
5. **Permission Checks**: Multiple layers of permission checking

## Future Enhancements

1. **Email Integration**: Send notifications via email
2. **Push Notifications**: Real-time push notifications
3. **Webhook Support**: External system integration
4. **Notification Templates**: Customizable notification templates
5. **Bulk Operations**: Advanced bulk notification management
6. **Analytics**: Notification delivery and read rate analytics

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure user has correct role and token
2. **Payment Notifications Not Visible**: Only admin users can see payment notifications
3. **Signals Not Triggering**: Ensure apps.py imports signals properly
4. **Role Detection Issues**: Check user profiles are created correctly

### Debug Commands
```bash
# Check user role
python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
User = get_user_model()
user = User.objects.get(username='your_username')
print(Notification.get_user_role(user))
"

# List all notifications for a user
python manage.py shell -c "
from apps.notifications.utils import get_user_notifications
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='your_username')
notifications = get_user_notifications(user)
for n in notifications:
    print(f'{n.title} - {n.notification_type} - {n.recipient_role}')
"
```
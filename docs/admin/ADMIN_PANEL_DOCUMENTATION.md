# Admin Panel and Payment System Documentation

## Overview

This document describes the custom admin panel and monthly payment tracking system implemented for the CodeSchool backend project.

## Features

### 1. Custom Admin Panel
- **Custom Django app** (`apps.admin_panel`) separate from Django's default admin
- **REST API endpoints** for managing all aspects of the system
- **Admin-only access** with proper permission controls
- **Comprehensive dashboard** with overview statistics

### 2. Monthly Payment Tracking System
- **Automated payment generation** for all students each month
- **Payment status tracking** (pending, paid, overdue, cancelled)
- **Overdue payment detection** and automatic status updates
- **Payment history and reporting**

## API Endpoints

All admin panel endpoints are prefixed with `/api/admin-panel/` and require admin authentication (is_staff=True or is_superuser=True).

### Dashboard
- `GET /api/admin-panel/dashboard/` - Get admin dashboard overview

### Payment Management
- `GET /api/admin-panel/payments/` - List all payments (with filtering)
- `POST /api/admin-panel/payments/` - Create new payment
- `GET /api/admin-panel/payments/{id}/` - Get payment details
- `PUT /api/admin-panel/payments/{id}/` - Update payment
- `DELETE /api/admin-panel/payments/{id}/` - Delete payment
- `POST /api/admin-panel/payments/{id}/mark_paid/` - Mark payment as paid
- `POST /api/admin-panel/payments/create_monthly_payments/` - Create monthly payments for all students
- `POST /api/admin-panel/payments/update_overdue/` - Update overdue payment statuses
- `GET /api/admin-panel/payments/payment_statistics/` - Get payment statistics

### Student Management
- `GET /api/admin-panel/students/` - List all students
- `POST /api/admin-panel/students/` - Create new student
- `GET /api/admin-panel/students/{id}/` - Get student details
- `PUT /api/admin-panel/students/{id}/` - Update student
- `DELETE /api/admin-panel/students/{id}/` - Delete student

### Teacher Management
- `GET /api/admin-panel/teachers/` - List all teachers
- `POST /api/admin-panel/teachers/` - Create new teacher
- `GET /api/admin-panel/teachers/{id}/` - Get teacher details
- `PUT /api/admin-panel/teachers/{id}/` - Update teacher
- `DELETE /api/admin-panel/teachers/{id}/` - Delete teacher

### Group Management
- `GET /api/admin-panel/groups/` - List all groups
- `POST /api/admin-panel/groups/` - Create new group
- `GET /api/admin-panel/groups/{id}/` - Get group details
- `PUT /api/admin-panel/groups/{id}/` - Update group
- `DELETE /api/admin-panel/groups/{id}/` - Delete group

### Course Management
- `GET /api/admin-panel/courses/` - List all courses
- `POST /api/admin-panel/courses/` - Create new course
- `GET /api/admin-panel/courses/{id}/` - Get course details
- `PUT /api/admin-panel/courses/{id}/` - Update course
- `DELETE /api/admin-panel/courses/{id}/` - Delete course

### Student Payment Summary
- `GET /api/admin-panel/student-payment-summary/{student_id}/` - Get payment summary for specific student

## Payment Model

The `Payment` model tracks monthly payments with the following key fields:

- `student` - ForeignKey to User (the student)
- `group` - ForeignKey to Group
- `course` - ForeignKey to Course (optional)
- `amount` - Payment amount (Decimal)
- `due_date` - When payment is due
- `paid_date` - When payment was made (null if unpaid)
- `month` - Payment month (1-12)
- `year` - Payment year
- `status` - Payment status (pending, paid, overdue, cancelled)
- `payment_method` - How payment was made
- `processed_by` - Admin who processed the payment
- `notes` - Additional notes

### Key Features:
- **Unique constraint** on student/group/month/year to prevent duplicates
- **Automatic overdue detection** based on due_date
- **Database indexes** for optimal query performance
- **Helper methods** for common operations

## Management Commands

### Create Monthly Payments
```bash
python manage.py create_monthly_payments --month 1 --year 2025 --amount 100.00
```
- Creates payment records for all active students
- `--dry-run` flag to preview without creating
- Defaults to current month/year if not specified

### Update Overdue Payments
```bash
python manage.py update_overdue_payments
```
- Updates pending payments past due date to overdue status
- `--dry-run` flag to preview changes
- `--verbose` flag for detailed output

### Payment Reports
```bash
python manage.py payment_report --month 1 --year 2025
```
- Generates comprehensive payment reports
- `--group` flag to filter by specific group
- `--overdue-only` flag to show only overdue payments
- `--summary-only` flag for statistics only

## How Monthly Payment Tracking Works

### 1. Payment Generation
- At the beginning of each month, run the `create_monthly_payments` command
- This creates a `Payment` record for each student in each group they belong to
- Payments are due by the 15th of the month (or last day if month has fewer than 15 days)

### 2. Payment Processing
- When a student pays, admin marks the payment as paid via API or admin interface
- Payment status changes from 'pending' to 'paid'
- Payment date and method are recorded
- Admin who processed the payment is tracked

### 3. Overdue Detection
- Run `update_overdue_payments` command daily (can be automated via cron)
- Any pending payments past their due date are marked as 'overdue'
- Overdue payments can trigger notifications or access restrictions

### 4. Reporting
- Comprehensive payment statistics available via API
- Group-wise breakdown of payment status
- Individual student payment summaries
- Outstanding amounts and payment rates

## Permission System

### Admin Users
- Must have `is_staff=True` or `is_superuser=True`
- Can access all admin panel endpoints
- Can manage payments, students, teachers, groups, and courses

### Regular Users
- Can only access their own payment summary
- Cannot access admin panel endpoints

## Example Usage

### Creating Monthly Payments
```python
# Via management command
python manage.py create_monthly_payments --month 2 --year 2025 --amount 150.00

# Via API
POST /api/admin-panel/payments/create_monthly_payments/
{
    "month": 2,
    "year": 2025,
    "amount": "150.00"
}
```

### Marking Payment as Paid
```python
POST /api/admin-panel/payments/123/mark_paid/
{
    "payment_method": "cash",
    "notes": "Paid in full on time"
}
```

### Getting Payment Statistics
```python
GET /api/admin-panel/payments/payment_statistics/
```

Returns:
```json
{
    "overall": {
        "total_payments": 100,
        "paid_payments": 75,
        "pending_payments": 20,
        "overdue_payments": 5,
        "total_amount": 10000.00,
        "paid_amount": 7500.00,
        "outstanding_amount": 2500.00
    },
    "current_month": {
        "month": 1,
        "year": 2025,
        "total_payments": 25,
        "paid_payments": 15,
        "pending_payments": 8,
        "overdue_payments": 2
    }
}
```

## Database Schema

The Payment model uses the following database indexes for performance:
- `(status, due_date)` - For finding overdue payments
- `(month, year)` - For monthly queries
- `(student, status)` - For student-specific queries

## Security Considerations

- All admin endpoints require authentication and admin permissions
- Payment processing is logged with admin user tracking
- Sensitive payment data is properly protected
- API rate limiting should be implemented for production use

## Future Enhancements

1. **Payment Gateway Integration** - Add support for online payments (Stripe, PayPal)
2. **Email Notifications** - Send payment reminders and receipts
3. **Bulk Payment Processing** - Import payments from CSV/Excel files
4. **Advanced Reporting** - Export reports to PDF/Excel
5. **Payment Plans** - Support for installment payments
6. **Automated Recurring Payments** - Set up automatic payment generation
7. **Financial Dashboard** - Real-time financial analytics
8. **Mobile App Support** - Dedicated mobile endpoints for payment management

## Testing

The admin panel includes comprehensive tests covering:
- Payment model functionality
- API endpoint security
- Monthly payment generation
- Overdue payment detection
- Payment status updates
- Permission enforcement

Run tests with:
```bash
python manage.py test apps.admin_panel
```

## Migration

The Payment model has been properly migrated and is ready for use. The migration includes:
- Table creation with proper indexes
- Foreign key relationships
- Unique constraints
- Default values

## Conclusion

The custom admin panel provides a comprehensive solution for managing the CodeSchool platform with robust payment tracking capabilities. The system is designed to be scalable, secure, and easy to use for administrative tasks.
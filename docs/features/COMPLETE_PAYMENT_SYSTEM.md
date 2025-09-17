# Complete Payment System Documentation

## Overview
This document provides a comprehensive overview of the custom admin panel and payment tracking system implemented in the CodeSchool Backend Django application.

## System Architecture

### 1. Custom Admin Panel (`apps/admin_panel/`)
- **Purpose**: Replace Django's default admin with a custom, API-driven admin panel
- **Components**: Models, Views, Serializers, APIs
- **Access**: Admin-only access with proper permissions

### 2. Payment Tracking System
- **Full Payment Support**: Complete payment processing
- **Partial Payment Support**: Track payments made in installments
- **Multi-Month Default Handling**: Automated student status management
- **Overdue Detection**: Automatic identification of late payments

## Core Models

### Payment Model
```python
class Payment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey('accounts.Group', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    month = models.IntegerField()
    year = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def remaining_amount(self):
        return self.amount - self.paid_amount

    def add_payment(self, amount):
        # Handles partial and full payment logic
```

### StudentPaymentStatus Model
```python
class StudentPaymentStatus(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    consecutive_unpaid_months = models.IntegerField(default=0)
    last_payment_date = models.DateField(null=True, blank=True)
    suspension_date = models.DateField(null=True, blank=True)
    warning_sent_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
```

## Key Features

### 1. Partial Payment Processing
- **Add Partial Payments**: API endpoint to add payments in installments
- **Automatic Status Updates**: Status changes from pending → partially_paid → paid
- **Remaining Balance Tracking**: Real-time calculation of outstanding amounts

### 2. Student Status Management
- **Active**: Student is current with payments
- **Warning**: Student has 1 unpaid month (grace period)
- **Suspended**: Student has 2+ unpaid months (access restricted)
- **Expelled**: Student has been permanently removed
- **Graduated**: Student has completed all courses

### 3. Automated Processing
- **Daily Status Updates**: Management command runs daily to check payment status
- **Monthly Billing**: Automatic creation of new payment records
- **Overdue Detection**: Automatic flagging of late payments

## API Endpoints

### Payment Management
- `GET /api/admin-panel/payments/` - List all payments
- `POST /api/admin-panel/payments/` - Create new payment
- `POST /api/admin-panel/payments/{id}/add_partial_payment/` - Add partial payment
- `GET /api/admin-panel/payments/students_at_risk/` - Get students with payment issues

### Student Status Management
- `GET /api/admin-panel/student-status/` - List all student statuses
- `PUT /api/admin-panel/student-status/{id}/` - Update student status

## Management Commands

### Daily Automation
```bash
python manage.py update_student_statuses
```
- Updates student payment statuses based on overdue payments
- Sends warnings for 1-month overdue
- Suspends access for 2+ months overdue
- Tracks consecutive unpaid months

### Testing Commands
```bash
# Dry run to see what would happen
python manage.py update_student_statuses --dry-run

# Force update all statuses
python manage.py update_student_statuses --force
```

## Business Logic

### Payment Flow
1. **Payment Creation**: Admin creates payment record for student
2. **Payment Processing**: Student makes payment (full or partial)
3. **Status Updates**: System automatically updates payment and student status
4. **Overdue Handling**: Automated detection and status progression

### Status Progression
```
Active → Warning (1 month overdue) → Suspended (2+ months) → Expelled (manual)
```

### Partial Payment Logic
- Payments can be made in multiple installments
- Each partial payment updates `paid_amount`
- Status automatically changes based on percentage paid
- Remaining balance is calculated in real-time

## Security Features
- **Admin-Only Access**: All admin panel endpoints require admin permissions
- **Token Authentication**: Secure API access using DRF tokens
- **Input Validation**: Comprehensive validation of payment data
- **Audit Trail**: Complete tracking of payment history and status changes

## Database Design
- **Normalized Structure**: Proper foreign key relationships
- **Decimal Precision**: Financial calculations using Decimal fields
- **Indexing**: Optimized queries for payment lookups
- **Constraints**: Data integrity through model validations

## Testing Coverage
- **Unit Tests**: Complete test coverage for models and views
- **Integration Tests**: End-to-end testing of payment flows
- **Edge Cases**: Testing for boundary conditions and error handling
- **Performance Tests**: Validation of query efficiency

## Deployment Considerations
- **Environment Variables**: Secure configuration management
- **Database Migrations**: Automated schema updates
- **Static Files**: Proper handling of admin panel assets
- **Monitoring**: Logging and error tracking

## Usage Examples

### Adding a Partial Payment
```python
# API call to add $50 to a $100 payment
POST /api/admin-panel/payments/123/add_partial_payment/
{
    "amount": "50.00"
}

# Response includes updated payment status and remaining balance
```

### Checking Students at Risk
```python
# Get list of students with payment issues
GET /api/admin-panel/payments/students_at_risk/

# Returns students with overdue payments or partial payments
```

### Running Daily Automation
```bash
# Add to crontab for daily execution at 2 AM
0 2 * * * cd /path/to/project && python manage.py update_student_statuses
```

## Performance Optimizations
- **Query Optimization**: Use of select_related and prefetch_related
- **Database Indexing**: Optimized indexes on frequently queried fields
- **Caching**: Strategic caching of payment summaries
- **Pagination**: Efficient handling of large payment lists

## Future Enhancements
- **Payment Reminders**: Email notifications for overdue payments
- **Payment Plans**: Flexible installment scheduling
- **Reporting Dashboard**: Visual analytics for payment trends
- **Mobile API**: Mobile app integration for payment processing

## Troubleshooting
- **Payment Calculation Issues**: Check decimal field precision
- **Status Not Updating**: Verify management command is running
- **Permission Errors**: Ensure proper admin permissions are set
- **Database Locks**: Monitor for long-running payment operations

This system provides a complete, production-ready payment management solution with comprehensive partial payment support and automated student status tracking.
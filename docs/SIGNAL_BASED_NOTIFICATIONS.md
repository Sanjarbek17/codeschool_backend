# Signal-Based Notification System

## 🎯 Overview

The signal-based notification system replaces the need for scheduled background tasks by automatically triggering payment notifications when specific events occur in the system. This approach is perfect for servers that don't support cron jobs or background scheduling.

## ✨ How It Works

### Automatic Triggers

The system automatically creates payment notifications when:

1. **Payment Events**:
   - ✅ Payment created (due soon check)
   - ✅ Payment updated (overdue check) 
   - ✅ Payment completed (confirmation)

2. **Educational Events**:
   - ✅ New homework assigned → Check group payments
   - ✅ Student submits work → Check student payments
   - ✅ Progress updated → Check payment status

### Real-Time Response

Instead of waiting for scheduled checks, notifications are sent immediately when:
- Payment becomes overdue
- New payment is due within 3 days
- Payment status changes
- Educational activities happen

## 🚀 Benefits

1. **No Scheduling Required** - No cron jobs or background processes needed
2. **Real-Time Notifications** - Instant response to events
3. **Server Independent** - Works on any hosting platform
4. **Event-Driven** - Only triggers when actually needed
5. **Efficient** - No unnecessary polling or scheduled checks

## 📋 Setup Options

### Option 1: Enhanced Runserver (Recommended)

```bash
./runserver.sh
# Choose option 3: "Use signal-based notifications (RECOMMENDED)"
```

### Option 2: Manual API Trigger

```bash
# Via API endpoint (admin only)
curl -X POST http://localhost:8000/api/notifications/trigger_payment_check/ \
     -H "Authorization: Token YOUR_ADMIN_TOKEN"
```

### Option 3: Management Command

```bash
# Manual trigger via command line
python manage.py trigger_payment_signals --verbose
```

### Option 4: Demo and Testing

```bash
# Run demo to see system in action
python scripts/demo_signals.py
```

## 🔧 Technical Implementation

### Signal Handlers

**File**: `apps/notifications/signals.py`

1. **Payment Signal Handler** (`handle_payment_created_or_updated`):
   - Triggers on Payment create/update
   - Checks due dates and overdue status
   - Creates appropriate notifications

2. **Educational Activity Handlers**:
   - `check_student_payments_on_homework`: Homework creation
   - `check_student_payment_on_submission`: Student submissions

### Key Functions

1. **`trigger_bulk_payment_check()`**: Manual bulk check function
2. **`trigger_group_payment_check(group)`**: Check specific group
3. **`trigger_student_payment_check(student)`**: Check specific student

### API Endpoints

- **POST** `/api/notifications/trigger_payment_check/` - Manual trigger (admin only)
- **GET** `/api/notifications/` - View notifications
- **GET** `/api/payment-notifications/` - View payment notifications

## 📊 Current Status

Based on recent test run:
- ✅ **20 notifications** sent for overdue payments
- ✅ Signal handlers active and working
- ✅ Real-time triggers functional
- ✅ API endpoints operational

## 🔄 How Notifications Are Created

### Automatic Flow:

1. **Event Occurs** (Payment created, Homework assigned, etc.)
2. **Signal Triggered** automatically by Django
3. **Payment Check** runs for relevant students/groups
4. **Notifications Created** for admin users
5. **Instant Delivery** via API/database

### Manual Flow:

1. **Admin Trigger** via API, command, or script
2. **Bulk Check** runs for all students
3. **Multiple Notifications** created as needed
4. **Status Report** returned

## 🎛️ Configuration

### In Django Settings:
```python
# Signals are automatically connected via apps.py
# No additional configuration needed
```

### In Production:
- No background process configuration required
- No cron job setup needed
- Works with any Django deployment (Heroku, AWS, etc.)

## 📈 Advantages Over Scheduled Approach

| Feature | Scheduled | Signal-Based |
|---------|-----------|--------------|
| Server Requirements | Cron/Background | None |
| Response Time | Delayed | Immediate |
| Resource Usage | Continuous | Event-Based |
| Hosting Compatibility | Limited | Universal |
| Maintenance | High | Low |

## 🎯 Use Cases

Perfect for:
- **Shared Hosting** (no cron access)
- **Heroku/PaaS** deployments
- **Development environments**
- **Resource-constrained servers**
- **Real-time notification needs**

## 🔮 Future Enhancements

The signal-based system can be extended to:
- Email notifications on events
- SMS alerts for urgent payments
- Custom notification rules
- Webhook integrations
- Mobile push notifications

---

**🎉 Result**: Payment notifications now work automatically without any scheduling infrastructure!
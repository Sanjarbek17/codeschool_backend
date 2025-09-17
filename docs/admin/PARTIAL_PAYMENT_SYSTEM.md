# Partial Payment & Multi-Month Default System Documentation

## 🎯 **Overview**

This documentation explains the enhanced payment system that supports:
1. **Partial Payments** - Students can pay in installments
2. **Multi-Month Default Tracking** - Monitor students who haven't paid for multiple months
3. **Automatic Status Management** - Students get warnings, suspended, or expelled based on payment history

---

## 💰 **Partial Payment Logic**

### **How It Works:**

1. **Payment Creation**: Each month, create payments with `amount` (total due) and `paid_amount` (starts at 0)
2. **Partial Payment**: Students can pay any amount up to the remaining balance
3. **Status Updates**: Payment status changes automatically based on paid amount

### **Payment Status Flow:**
```
PENDING → PARTIALLY_PAID → PAID
    ↓
OVERDUE (if due date passes)
```

### **Example Scenario:**
```python
# Student owes $100 for January
payment = Payment.objects.create(
    student=student_user,
    group=group,
    amount=Decimal('100.00'),  # Total due
    paid_amount=Decimal('0.00'), # Initially nothing paid
    status='pending'
)

# Student pays $50
payment.add_payment(amount=Decimal('50.00'), payment_method='cash')
# Now: paid_amount=50.00, remaining_amount=50.00, status='partially_paid'

# Student pays remaining $50
payment.add_payment(amount=Decimal('50.00'), payment_method='cash')  
# Now: paid_amount=100.00, remaining_amount=0.00, status='paid'
```

---

## 📅 **Multi-Month Default Tracking**

### **What Happens When Students Don't Pay:**

| Unpaid Months | Status | Action |
|---------------|--------|---------|
| **1 month** | `active` | No action |
| **2 months** | `warning` | Send payment reminder |
| **3 months** | `suspended` | Suspend from classes |
| **4+ months** | `expelled` | Remove from system |

### **Automatic Status Updates:**

The system tracks each student's payment history and updates their status automatically:

```python
# StudentPaymentStatus model tracks:
- consecutive_unpaid_months: How many months in a row without payment
- total_debt: Total amount owed across all unpaid payments  
- last_payment_date: When they last made any payment
- status: Current status (active/warning/suspended/expelled)
```

---

## 🔧 **API Endpoints**

### **Partial Payment Endpoints:**

1. **Add Partial Payment:**
```http
POST /api/admin-panel/payments/{id}/add_partial_payment/
{
    "amount": "50.00",
    "payment_method": "cash",
    "notes": "Partial payment received"
}
```

2. **Get Students At Risk:**
```http
GET /api/admin-panel/payments/students_at_risk/?min_months=2
```

3. **Get Suspension Candidates:**
```http
GET /api/admin-panel/payments/suspension_candidates/
```

4. **Student Payment Status Management:**
```http
GET /api/admin-panel/payment-statuses/
POST /api/admin-panel/payment-statuses/{id}/suspend_student/
POST /api/admin-panel/payment-statuses/{id}/reactivate_student/
```

---

## 🤖 **Automation (Daily Tasks)**

### **Management Commands:**

1. **Update Overdue Payments** (Run daily):
```bash
python manage.py update_overdue_payments
```

2. **Update Student Statuses** (Run daily):
```bash
python manage.py update_student_statuses
```

3. **Create Monthly Payments** (Run monthly):
```bash
python manage.py create_monthly_payments --month 2 --year 2025
```

### **Recommended Cron Jobs:**
```bash
# Daily at 1 AM - Update overdue payments
0 1 * * * /path/to/python /path/to/manage.py update_overdue_payments

# Daily at 2 AM - Update student statuses  
0 2 * * * /path/to/python /path/to/manage.py update_student_statuses

# Monthly on 1st at 9 AM - Create new payments
0 9 1 * * /path/to/python /path/to/manage.py create_monthly_payments
```

---

## 📊 **Example Scenarios**

### **Scenario 1: Student Pays Partially**
```
Month 1: Student owes $100
- Pays $60 → Status: "partially_paid", remaining: $40
- Due date passes → Status: "overdue" (still owes $40)

Month 2: New payment created for $100  
- Student pays remaining $40 from Month 1 → Month 1 becomes "paid"
- Student pays $30 for Month 2 → Month 2 status: "partially_paid"

Total debt: $70 (remaining from Month 2)
```

### **Scenario 2: Student Doesn't Pay for 3 Months**
```
January: $100 unpaid → Status: "pending" → "overdue"
February: $100 unpaid → Status: "pending" → "overdue"  
March: $100 unpaid → Status: "pending" → "overdue"

Student Status Updates:
- After Month 2: Status = "warning", send reminder
- After Month 3: Status = "suspended", cannot attend classes
- Total debt: $300
```

### **Scenario 3: Student Catches Up**
```
Student was suspended with 3 unpaid months ($300 debt)
- Pays $300 in full
- Status automatically changes back to "active"
- Can resume classes
```

---

## 🛠 **Database Changes**

### **New Payment Model Fields:**
```python
class Payment(models.Model):
    # Existing fields...
    amount = models.DecimalField(...)  # Total amount due
    paid_amount = models.DecimalField(default=0)  # Amount paid so far
    status = models.CharField(max_length=15)  # Now includes "partially_paid"
    
    @property
    def remaining_amount(self):
        return self.amount - self.paid_amount
```

### **New StudentPaymentStatus Model:**
```python
class StudentPaymentStatus(models.Model):
    student = models.OneToOneField(User)
    status = models.CharField(choices=[
        ('active', 'Active'),
        ('warning', 'Payment Warning'), 
        ('suspended', 'Suspended'),
        ('expelled', 'Expelled')
    ])
    consecutive_unpaid_months = models.PositiveIntegerField()
    total_debt = models.DecimalField()
    last_payment_date = models.DateField()
    suspension_date = models.DateField()
```

---

## 🎮 **How to Use**

### **For Admins:**

1. **Process Partial Payment:**
   - Go to payment record
   - Use "Add Partial Payment" action
   - Enter amount and payment method
   - System automatically updates status

2. **Monitor At-Risk Students:**
   - Check `/api/admin-panel/payments/students_at_risk/`
   - Review students with 2+ unpaid months
   - Send warnings or reminders

3. **Handle Suspensions:**
   - Review suspension candidates
   - Use suspend/reactivate actions
   - Track suspension dates

### **Daily Workflow:**
```
1. Run update_overdue_payments (automatically marks overdue)
2. Run update_student_statuses (updates warnings/suspensions)
3. Review at-risk students list
4. Process any partial payments received
5. Send warnings to students in "warning" status
```

---

## 🔍 **Monitoring & Reports**

### **Key Metrics to Track:**
- Students with 2+ unpaid months (at risk)
- Students with 3+ unpaid months (suspension candidates)
- Total outstanding debt
- Average debt per student
- Payment completion rates

### **Alerts to Set Up:**
- Daily: New students reaching 2+ unpaid months
- Weekly: Students approaching suspension (3+ months)
- Monthly: Total debt summary

---

## ⚠️ **Important Notes**

1. **Partial payments don't reset overdue status** - student still needs to complete payment
2. **Suspension is automatic** after 3+ unpaid months
3. **Reactivation requires manual action** by admin after payment
4. **Payment status is tracked per student globally**, not per group
5. **Multiple group enrollments multiply debt** - each group = separate payment

This system provides comprehensive tracking and automation for handling partial payments and multi-month defaults while maintaining clear student status progression.
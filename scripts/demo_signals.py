#!/usr/bin/env python3
"""
Demo script to trigger payment notifications using signals
This replaces the scheduled approach with event-driven notifications
"""

import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
project_root = "/Volumes/Transcend/backend/codeschool_backend"
sys.path.append(project_root)
os.chdir(project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.core.management import call_command
from apps.notifications.signals import trigger_bulk_payment_check
from apps.admin_panel.models import Payment


def demo_signal_notifications():
    """
    Demo function to show how signal-based notifications work
    """
    print("🚀 Signal-Based Payment Notification Demo")
    print("=" * 50)

    # 1. Manual bulk check
    print("\n1️⃣ Running manual bulk payment check...")
    notifications_sent = trigger_bulk_payment_check()
    print(f"   📧 Sent {notifications_sent} notifications")

    # 2. Show how signals work automatically
    print("\n2️⃣ Signal triggers:")
    print("   ✅ When Payment is created/updated → Automatic notification")
    print("   ✅ When Homework is created → Check group payments")
    print("   ✅ When Student submits → Check student payments")
    print("   ✅ When Progress updates → Check payment status")

    # 3. Show current payment status
    print("\n3️⃣ Current payment overview:")
    today = timezone.now().date()

    # Upcoming payments
    upcoming = Payment.objects.filter(
        due_date__lte=today + timedelta(days=3),
        due_date__gte=today,
        status__in=["pending", "partially_paid"],
    ).count()

    # Overdue payments
    overdue = Payment.objects.filter(
        due_date__lt=today, status__in=["pending", "partially_paid"]
    ).count()

    print(f"   📅 Upcoming payments (next 3 days): {upcoming}")
    print(f"   ⚠️  Overdue payments: {overdue}")

    # 4. Manual trigger options
    print("\n4️⃣ Manual trigger options:")
    print("   🔧 Management command: python manage.py trigger_payment_signals")
    print("   🌐 API endpoint: POST /api/notifications/trigger_payment_check/")
    print(
        "   🐍 Python function: from apps.notifications.signals import trigger_bulk_payment_check"
    )

    print("\n✨ Signal-based notifications are now active!")
    print("   No scheduling needed - notifications trigger automatically on events!")


if __name__ == "__main__":
    demo_signal_notifications()

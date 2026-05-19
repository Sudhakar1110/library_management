"""
library_management.tasks
~~~~~~~~~~~~~~~~~~~~~~~~~
Scheduled background tasks.
"""

import frappe
from frappe.utils import today, add_days


def send_overdue_reminders():
    """Daily task: email members whose books are due soon or overdue."""
    settings = frappe.get_single("Library Settings")
    if not settings.send_overdue_reminders:
        return

    reminder_date = add_days(today(), settings.reminder_days_before_due)

    # Books due on `reminder_date` (upcoming)
    upcoming = frappe.db.sql(
        """
        SELECT bt.name, bt.library_member, bt.member_name, bt.book_title, bt.due_date,
               lm.email
        FROM `tabBook Transaction` bt
        JOIN `tabLibrary Member` lm ON lm.name = bt.library_member
        WHERE bt.transaction_type = 'Issue'
          AND bt.docstatus = 1
          AND DATE(bt.due_date) = %s
          AND lm.email IS NOT NULL AND lm.email != ''
          AND NOT EXISTS (
              SELECT 1 FROM `tabBook Transaction` ret
              WHERE ret.transaction_type = 'Return'
                AND ret.library_member = bt.library_member
                AND ret.book = bt.book
                AND ret.docstatus = 1
          )
        """,
        (reminder_date,),
        as_dict=True,
    )

    for row in upcoming:
        frappe.sendmail(
            recipients=[row.email],
            subject=f"Reminder: Book Due Soon — {row.book_title}",
            message=(
                f"Dear {row.member_name},<br><br>"
                f"This is a reminder that <b>{row.book_title}</b> is due on "
                f"<b>{row.due_date}</b>. Please return it on time to avoid fines.<br><br>"
                "Thank you,<br>Library Management System"
            ),
        )
        frappe.logger("library_management").info(
            f"Sent due-date reminder to {row.email} for {row.book_title}"
        )

    # Overdue books
    overdue = frappe.db.sql(
        """
        SELECT bt.name, bt.library_member, bt.member_name, bt.book_title, bt.due_date,
               lm.email, DATEDIFF(CURDATE(), bt.due_date) AS overdue_days
        FROM `tabBook Transaction` bt
        JOIN `tabLibrary Member` lm ON lm.name = bt.library_member
        WHERE bt.transaction_type = 'Issue'
          AND bt.docstatus = 1
          AND bt.due_date < CURDATE()
          AND lm.email IS NOT NULL AND lm.email != ''
          AND NOT EXISTS (
              SELECT 1 FROM `tabBook Transaction` ret
              WHERE ret.transaction_type = 'Return'
                AND ret.library_member = bt.library_member
                AND ret.book = bt.book
                AND ret.docstatus = 1
          )
        """,
        as_dict=True,
    )

    fine_per_day = settings.fine_per_day
    for row in overdue:
        fine = row.overdue_days * fine_per_day
        frappe.sendmail(
            recipients=[row.email],
            subject=f"Overdue Notice: {row.book_title}",
            message=(
                f"Dear {row.member_name},<br><br>"
                f"<b>{row.book_title}</b> was due on <b>{row.due_date}</b> and is now "
                f"<b>{row.overdue_days} day(s) overdue</b>.<br>"
                f"Accumulated fine: <b>{fine}</b>.<br><br>"
                "Please return the book as soon as possible.<br><br>"
                "Library Management System"
            ),
        )

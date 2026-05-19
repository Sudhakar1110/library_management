import frappe


def execute():
    """Create default Library Settings if not exists."""
    if not frappe.db.exists("Library Settings", "Library Settings"):
        doc = frappe.new_doc("Library Settings")
        doc.loan_period_days = 14
        doc.fine_per_day = 5.0
        doc.max_books_per_member = 3
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

import frappe


def before_tests():
    """Called before test suite runs — set up required fixtures."""
    frappe.db.truncate("Book Transaction")
    frappe.db.truncate("Book")
    frappe.db.truncate("Library Member")

    # Ensure settings exist
    if not frappe.db.exists("Library Settings", "Library Settings"):
        doc = frappe.new_doc("Library Settings")
        doc.loan_period_days = 14
        doc.fine_per_day = 5
        doc.max_books_per_member = 3
        doc.insert(ignore_permissions=True)

    frappe.db.commit()

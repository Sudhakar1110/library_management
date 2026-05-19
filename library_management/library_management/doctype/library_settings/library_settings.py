import frappe
from frappe.model.document import Document


class LibrarySettings(Document):
    def validate(self):
        if self.loan_period_days <= 0:
            frappe.throw("Loan Period must be greater than 0.")
        if self.fine_per_day < 0:
            frappe.throw("Fine Per Day cannot be negative.")
        if self.max_books_per_member <= 0:
            frappe.throw("Max Books Per Member must be at least 1.")
        if self.reminder_days_before_due < 0:
            frappe.throw("Reminder days cannot be negative.")

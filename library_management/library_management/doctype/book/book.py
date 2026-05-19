import frappe
from frappe.model.document import Document


class Book(Document):
    # ---------- Frappe Lifecycle Hooks ----------

    def validate(self):
        self._validate_isbn()
        self._validate_copies()

    def before_insert(self):
        """On first insert set available_copies = total_copies."""
        self.available_copies = self.total_copies

    def after_insert(self):
        frappe.msgprint(
            f"Book <b>{self.title}</b> added to catalog successfully.",
            alert=True,
        )

    # ---------- Private Helpers ----------

    def _validate_isbn(self):
        """Basic ISBN-10 / ISBN-13 length check."""
        isbn = (self.isbn or "").replace("-", "").replace(" ", "")
        if isbn and len(isbn) not in (10, 13):
            frappe.throw(
                f"ISBN <b>{self.isbn}</b> must be 10 or 13 digits (got {len(isbn)})."
            )

    def _validate_copies(self):
        if self.total_copies < 0:
            frappe.throw("Total Copies cannot be negative.")
        if self.available_copies is not None and self.available_copies > self.total_copies:
            frappe.throw("Available Copies cannot exceed Total Copies.")

    # ---------- Public Methods ----------

    def increment_available(self):
        """Called when a book is returned."""
        if self.available_copies >= self.total_copies:
            frappe.throw(f"All copies of <b>{self.title}</b> are already available.")
        self.available_copies += 1
        self.save(ignore_permissions=True)

    def decrement_available(self):
        """Called when a book is issued."""
        if self.available_copies <= 0:
            frappe.throw(f"No available copies of <b>{self.title}</b>.")
        self.available_copies -= 1
        self.save(ignore_permissions=True)

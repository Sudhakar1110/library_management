import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, date_diff


class BookTransaction(Document):
    # ---------- Frappe Lifecycle Hooks ----------

    def validate(self):
        self._validate_member_active()
        if self.transaction_type == "Issue":
            self._validate_issue()
        elif self.transaction_type == "Return":
            self._validate_return()

    def before_submit(self):
        if self.transaction_type == "Issue":
            self._set_due_date()
        elif self.transaction_type == "Return":
            self._calculate_fine()

    def on_submit(self):
        if self.transaction_type == "Issue":
            self._issue_book()
        elif self.transaction_type == "Return":
            self._return_book()

    def on_cancel(self):
        if self.transaction_type == "Issue":
            self._cancel_issue()
        elif self.transaction_type == "Return":
            self._cancel_return()

    # ---------- Validation Helpers ----------

    def _validate_member_active(self):
        member = frappe.get_doc("Library Member", self.library_member)
        if not member.is_active():
            frappe.throw(
                _(
                    f"Member <b>{member.full_name}</b> is <b>{member.status}</b>. "
                    "Please renew membership before proceeding."
                )
            )

    def _validate_issue(self):
        member = frappe.get_doc("Library Member", self.library_member)
        member.can_borrow()

        book = frappe.get_doc("Book", self.book)
        if book.available_copies <= 0:
            frappe.throw(
                _(f"No available copies of <b>{book.title}</b> at the moment.")
            )

        # Check if member already has this book
        existing = frappe.db.exists(
            "Book Transaction",
            {
                "library_member": self.library_member,
                "book": self.book,
                "transaction_type": "Issue",
                "docstatus": 1,
                # No matching return yet
            },
        )
        if existing:
            # Check if there is no return for it
            returned = frappe.db.exists(
                "Book Transaction",
                {
                    "library_member": self.library_member,
                    "book": self.book,
                    "transaction_type": "Return",
                    "docstatus": 1,
                },
            )
            if not returned:
                frappe.throw(
                    _(
                        f"Member <b>{member.full_name}</b> already has "
                        f"<b>{book.title}</b> issued."
                    )
                )

    def _validate_return(self):
        # Ensure the book was actually issued to this member
        issued = frappe.db.get_value(
            "Book Transaction",
            {
                "library_member": self.library_member,
                "book": self.book,
                "transaction_type": "Issue",
                "docstatus": 1,
            },
            ["name", "issue_date", "due_date"],
            as_dict=True,
        )
        if not issued:
            frappe.throw(
                _(
                    f"No active issue found for <b>{self.book}</b> "
                    f"under member <b>{self.library_member}</b>."
                )
            )
        # Copy the original issue date for fine calculation
        self.issue_date = self.issue_date or issued.issue_date
        self.due_date = issued.due_date
        self.return_date = self.return_date or today()

    # ---------- Pre-Submit Helpers ----------

    def _set_due_date(self):
        if not self.due_date:
            settings = frappe.get_single("Library Settings")
            from frappe.utils import add_days
            self.due_date = add_days(self.issue_date, settings.loan_period_days)

    def _calculate_fine(self):
        if not self.return_date:
            self.return_date = today()
        if self.due_date and getdate(self.return_date) > getdate(self.due_date):
            settings = frappe.get_single("Library Settings")
            overdue_days = date_diff(self.return_date, self.due_date)
            self.fine_amount = overdue_days * settings.fine_per_day
        else:
            self.fine_amount = 0

    # ---------- Submit / Cancel Actions ----------

    def _issue_book(self):
        book = frappe.get_doc("Book", self.book)
        book.decrement_available()

        member = frappe.get_doc("Library Member", self.library_member)
        member.books_issued = (member.books_issued or 0) + 1
        member.save(ignore_permissions=True)

    def _return_book(self):
        book = frappe.get_doc("Book", self.book)
        book.increment_available()

        member = frappe.get_doc("Library Member", self.library_member)
        member.books_issued = max((member.books_issued or 1) - 1, 0)
        member.save(ignore_permissions=True)

    def _cancel_issue(self):
        """Reverse an issue — put the book back."""
        book = frappe.get_doc("Book", self.book)
        book.increment_available()

        member = frappe.get_doc("Library Member", self.library_member)
        member.books_issued = max((member.books_issued or 1) - 1, 0)
        member.save(ignore_permissions=True)

    def _cancel_return(self):
        """Reverse a return — mark book as out again."""
        book = frappe.get_doc("Book", self.book)
        book.decrement_available()

        member = frappe.get_doc("Library Member", self.library_member)
        member.books_issued = (member.books_issued or 0) + 1
        member.save(ignore_permissions=True)


# ── Module-level event handlers (called from hooks.py) ──────────────────────

def on_submit(doc, method=None):
    """Proxy hook — delegate to the class method."""
    pass  # Logic is already in Document.on_submit


def on_cancel(doc, method=None):
    """Proxy hook — delegate to the class method."""
    pass  # Logic is already in Document.on_cancel

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate


class LibraryMember(Document):
    # ---------- Frappe Lifecycle Hooks ----------

    def validate(self):
        self._validate_dates()
        self._update_status()

    def before_save(self):
        self._update_status()

    # ---------- Private Helpers ----------

    def _validate_dates(self):
        if (
            self.membership_start_date
            and self.membership_end_date
            and getdate(self.membership_end_date) < getdate(self.membership_start_date)
        ):
            frappe.throw("Membership End Date must be after Start Date.")

    def _update_status(self):
        if not self.membership_end_date:
            return
        if getdate(today()) > getdate(self.membership_end_date):
            self.status = "Expired"
        elif self.status != "Suspended":
            self.status = "Active"

    # ---------- Public Methods ----------

    def is_active(self):
        """Returns True if the member can borrow books."""
        self._update_status()
        return self.status == "Active"

    def can_borrow(self):
        """Check if member is allowed to borrow more books."""
        settings = frappe.get_single("Library Settings")
        if self.books_issued >= settings.max_books_per_member:
            frappe.throw(
                f"Member <b>{self.full_name}</b> has already reached the "
                f"maximum of <b>{settings.max_books_per_member}</b> books."
            )
        if not self.is_active():
            frappe.throw(
                f"Member <b>{self.full_name}</b> membership is <b>{self.status}</b>."
            )

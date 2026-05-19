"""
Tests for Library Management application.
Run with: bench --site your-site.local run-tests --app library_management
"""

import unittest
import frappe
from frappe.utils import today, add_days


def make_settings(loan_days=14, fine=5, max_books=3):
    if frappe.db.exists("Library Settings", "Library Settings"):
        s = frappe.get_single("Library Settings")
    else:
        s = frappe.new_doc("Library Settings")
    s.loan_period_days = loan_days
    s.fine_per_day = fine
    s.max_books_per_member = max_books
    s.save(ignore_permissions=True)
    frappe.db.commit()
    return s


def make_book(isbn="9780000000001", title="Test Book", copies=5):
    if frappe.db.exists("Book", {"isbn": isbn}):
        return frappe.get_doc("Book", {"isbn": isbn})
    doc = frappe.new_doc("Book")
    doc.isbn = isbn
    doc.title = title
    doc.author = "Test Author"
    doc.total_copies = copies
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


def make_member(full_name="Test Member", days=365):
    doc = frappe.new_doc("Library Member")
    doc.full_name = full_name
    doc.membership_type = "Standard"
    doc.membership_start_date = today()
    doc.membership_end_date = add_days(today(), days)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


class TestBook(unittest.TestCase):
    def setUp(self):
        self.book = make_book()

    def tearDown(self):
        frappe.delete_doc("Book", self.book.name, ignore_permissions=True, force=True)
        frappe.db.commit()

    def test_available_copies_set_on_insert(self):
        self.assertEqual(self.book.available_copies, self.book.total_copies)

    def test_invalid_isbn_raises(self):
        doc = frappe.new_doc("Book")
        doc.isbn = "123"  # too short
        doc.title = "Bad ISBN"
        doc.author = "Author"
        doc.total_copies = 1
        with self.assertRaises(frappe.ValidationError):
            doc.insert(ignore_permissions=True)

    def test_decrement_and_increment(self):
        initial = self.book.available_copies
        self.book.decrement_available()
        self.assertEqual(self.book.available_copies, initial - 1)
        self.book.increment_available()
        self.assertEqual(self.book.available_copies, initial)


class TestLibraryMember(unittest.TestCase):
    def setUp(self):
        self.member = make_member()

    def tearDown(self):
        frappe.delete_doc("Library Member", self.member.name, ignore_permissions=True, force=True)
        frappe.db.commit()

    def test_active_status(self):
        self.assertEqual(self.member.status, "Active")
        self.assertTrue(self.member.is_active())

    def test_expired_membership(self):
        self.member.membership_end_date = add_days(today(), -1)
        self.member.save(ignore_permissions=True)
        frappe.db.commit()
        self.member.reload()
        self.assertEqual(self.member.status, "Expired")

    def test_invalid_dates_raises(self):
        doc = frappe.new_doc("Library Member")
        doc.full_name = "Bad Dates Member"
        doc.membership_type = "Standard"
        doc.membership_start_date = today()
        doc.membership_end_date = add_days(today(), -10)
        with self.assertRaises(frappe.ValidationError):
            doc.insert(ignore_permissions=True)


class TestBookTransaction(unittest.TestCase):
    def setUp(self):
        make_settings()
        self.book = make_book(isbn="9780000000099", copies=3)
        self.member = make_member("Transaction Test Member")

    def tearDown(self):
        # Cancel and delete all transactions for this member+book
        for txn in frappe.get_all(
            "Book Transaction",
            filters={"library_member": self.member.name, "book": self.book.name},
        ):
            doc = frappe.get_doc("Book Transaction", txn.name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Book Transaction", txn.name, force=True)
        frappe.delete_doc("Library Member", self.member.name, force=True, ignore_permissions=True)
        frappe.delete_doc("Book", self.book.name, force=True, ignore_permissions=True)
        frappe.db.commit()

    def _issue(self):
        doc = frappe.new_doc("Book Transaction")
        doc.transaction_type = "Issue"
        doc.library_member = self.member.name
        doc.book = self.book.name
        doc.issue_date = today()
        doc.insert(ignore_permissions=True)
        doc.submit()
        frappe.db.commit()
        return doc

    def _return(self, return_date=None):
        doc = frappe.new_doc("Book Transaction")
        doc.transaction_type = "Return"
        doc.library_member = self.member.name
        doc.book = self.book.name
        doc.return_date = return_date or today()
        doc.insert(ignore_permissions=True)
        doc.submit()
        frappe.db.commit()
        return doc

    def test_issue_reduces_available_copies(self):
        initial = self.book.available_copies
        self._issue()
        self.book.reload()
        self.assertEqual(self.book.available_copies, initial - 1)

    def test_return_increases_available_copies(self):
        self._issue()
        self.book.reload()
        after_issue = self.book.available_copies
        self._return()
        self.book.reload()
        self.assertEqual(self.book.available_copies, after_issue + 1)

    def test_fine_calculated_on_late_return(self):
        issue = self._issue()
        settings = frappe.get_single("Library Settings")
        overdue_days = settings.loan_period_days + 5
        late_return_date = add_days(today(), overdue_days)
        ret = self._return(return_date=late_return_date)
        expected_fine = 5 * settings.fine_per_day
        self.assertEqual(ret.fine_amount, expected_fine)

    def test_no_fine_on_time_return(self):
        self._issue()
        ret = self._return()
        self.assertEqual(ret.fine_amount, 0)

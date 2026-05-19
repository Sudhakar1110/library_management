"""
library_management.api
~~~~~~~~~~~~~~~~~~~~~~
Public REST API endpoints (whitelisted for external / portal calls).
All endpoints require authentication unless noted.
"""

import frappe
from frappe import _
from frappe.utils import today, add_days


# ── Books ────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_available_books(genre=None, search=None):
    """Return a list of books that have at least one available copy.

    Query Params:
        genre  (str) -- Filter by genre (optional)
        search (str) -- Full-text search on title/author/isbn (optional)
    """
    filters = {"available_copies": [">", 0]}
    if genre:
        filters["genre"] = genre

    or_filters = None
    if search:
        or_filters = {
            "title": ["like", f"%{search}%"],
            "author": ["like", f"%{search}%"],
            "isbn": ["like", f"%{search}%"],
        }

    books = frappe.get_list(
        "Book",
        filters=filters,
        or_filters=or_filters,
        fields=["name", "isbn", "title", "author", "publisher", "genre",
                "available_copies", "total_copies", "cover_image"],
        order_by="title asc",
        ignore_permissions=False,
    )
    return books


@frappe.whitelist()
def get_book_detail(isbn):
    """Return full details of a single book by ISBN."""
    name = frappe.db.get_value("Book", {"isbn": isbn}, "name")
    if not name:
        frappe.throw(_("Book with ISBN {0} not found.").format(isbn), frappe.DoesNotExistError)
    return frappe.get_doc("Book", name).as_dict()


# ── Members ──────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_member_transactions(member_id, status=None):
    """Return all transactions for a given member.

    Args:
        member_id (str) -- Library Member docname
        status    (str) -- 'issued' | 'returned' | None for all
    """
    filters = {"library_member": member_id}
    if status == "issued":
        filters["transaction_type"] = "Issue"
        filters["docstatus"] = 1
    elif status == "returned":
        filters["transaction_type"] = "Return"
        filters["docstatus"] = 1

    transactions = frappe.get_list(
        "Book Transaction",
        filters=filters,
        fields=["name", "transaction_type", "book", "book_title", "book_author",
                "issue_date", "due_date", "return_date", "fine_amount", "fine_paid",
                "docstatus"],
        order_by="issue_date desc",
    )
    return transactions


# ── Transactions ─────────────────────────────────────────────────────────────

@frappe.whitelist()
def issue_book(member_id, isbn, issue_date=None):
    """Issue a book to a member.

    Args:
        member_id  (str)  -- Library Member docname
        isbn       (str)  -- Book ISBN
        issue_date (str)  -- ISO date string, defaults to today
    """
    book_name = frappe.db.get_value("Book", {"isbn": isbn}, "name")
    if not book_name:
        frappe.throw(_("Book with ISBN {0} not found.").format(isbn))

    doc = frappe.new_doc("Book Transaction")
    doc.transaction_type = "Issue"
    doc.library_member = member_id
    doc.book = book_name
    doc.issue_date = issue_date or today()
    doc.insert(ignore_permissions=False)
    doc.submit()
    frappe.db.commit()

    return {
        "transaction": doc.name,
        "due_date": doc.due_date,
        "message": f"Book '{doc.book_title}' issued successfully. Due on {doc.due_date}.",
    }


@frappe.whitelist()
def return_book(member_id, isbn, return_date=None):
    """Return a previously issued book.

    Args:
        member_id   (str) -- Library Member docname
        isbn        (str) -- Book ISBN
        return_date (str) -- ISO date string, defaults to today
    """
    book_name = frappe.db.get_value("Book", {"isbn": isbn}, "name")
    if not book_name:
        frappe.throw(_("Book with ISBN {0} not found.").format(isbn))

    doc = frappe.new_doc("Book Transaction")
    doc.transaction_type = "Return"
    doc.library_member = member_id
    doc.book = book_name
    doc.return_date = return_date or today()
    doc.insert(ignore_permissions=False)
    doc.submit()
    frappe.db.commit()

    response = {
        "transaction": doc.name,
        "fine_amount": doc.fine_amount,
        "message": f"Book '{doc.book_title}' returned successfully.",
    }
    if doc.fine_amount:
        response["message"] += f" Fine charged: {doc.fine_amount}."
    return response


# ── Dashboard / Reports ──────────────────────────────────────────────────────

@frappe.whitelist()
def get_overdue_books():
    """Return all currently overdue issues (not yet returned)."""
    issued_books = frappe.db.sql(
        """
        SELECT
            bt.name,
            bt.library_member,
            bt.member_name,
            bt.book,
            bt.book_title,
            bt.book_author,
            bt.issue_date,
            bt.due_date,
            DATEDIFF(CURDATE(), bt.due_date) AS overdue_days
        FROM `tabBook Transaction` bt
        WHERE bt.transaction_type = 'Issue'
          AND bt.docstatus = 1
          AND bt.due_date < CURDATE()
          AND NOT EXISTS (
              SELECT 1
              FROM `tabBook Transaction` ret
              WHERE ret.transaction_type = 'Return'
                AND ret.library_member = bt.library_member
                AND ret.book = bt.book
                AND ret.docstatus = 1
          )
        ORDER BY bt.due_date ASC
        """,
        as_dict=True,
    )
    return issued_books


@frappe.whitelist()
def get_dashboard_stats():
    """Return summary stats for the library dashboard."""
    total_books = frappe.db.count("Book")
    total_members = frappe.db.count("Library Member", {"status": "Active"})
    issued_count = frappe.db.sql(
        """
        SELECT COUNT(*) FROM `tabBook Transaction` bt
        WHERE bt.transaction_type = 'Issue' AND bt.docstatus = 1
          AND NOT EXISTS (
              SELECT 1 FROM `tabBook Transaction` ret
              WHERE ret.transaction_type = 'Return'
                AND ret.library_member = bt.library_member
                AND ret.book = bt.book
                AND ret.docstatus = 1
          )
        """
    )[0][0]
    overdue_count = frappe.db.sql(
        """
        SELECT COUNT(*) FROM `tabBook Transaction` bt
        WHERE bt.transaction_type = 'Issue' AND bt.docstatus = 1
          AND bt.due_date < CURDATE()
          AND NOT EXISTS (
              SELECT 1 FROM `tabBook Transaction` ret
              WHERE ret.transaction_type = 'Return'
                AND ret.library_member = bt.library_member
                AND ret.book = bt.book
                AND ret.docstatus = 1
          )
        """
    )[0][0]

    return {
        "total_books": total_books,
        "active_members": total_members,
        "books_issued": issued_count,
        "overdue_books": overdue_count,
    }

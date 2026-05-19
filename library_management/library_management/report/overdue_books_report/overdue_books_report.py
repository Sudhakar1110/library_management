"""Overdue Books Report — Script Report for Frappe v15 / ERPNext v15."""

import frappe


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "transaction",
            "label": "Transaction ID",
            "fieldtype": "Link",
            "options": "Book Transaction",
            "width": 150,
        },
        {
            "fieldname": "member_name",
            "label": "Member Name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "fieldname": "library_member",
            "label": "Member ID",
            "fieldtype": "Link",
            "options": "Library Member",
            "width": 130,
        },
        {
            "fieldname": "email",
            "label": "Email",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "fieldname": "book_title",
            "label": "Book Title",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "isbn",
            "label": "ISBN",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "fieldname": "issue_date",
            "label": "Issue Date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "fieldname": "due_date",
            "label": "Due Date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "fieldname": "overdue_days",
            "label": "Overdue Days",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "fieldname": "fine_accrued",
            "label": "Fine Accrued",
            "fieldtype": "Currency",
            "width": 120,
        },
    ]


def get_data(filters):
    conditions = ""
    if filters.get("library_member"):
        conditions += " AND bt.library_member = %(library_member)s"
    if filters.get("from_date"):
        conditions += " AND bt.due_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND bt.due_date <= %(to_date)s"

    settings = frappe.get_single("Library Settings")
    fine_per_day = settings.fine_per_day or 0

    rows = frappe.db.sql(
        f"""
        SELECT
            bt.name                            AS transaction,
            bt.member_name,
            bt.library_member,
            lm.email,
            bt.book_title,
            b.isbn,
            bt.issue_date,
            bt.due_date,
            DATEDIFF(CURDATE(), bt.due_date)   AS overdue_days
        FROM `tabBook Transaction` bt
        JOIN `tabLibrary Member` lm ON lm.name = bt.library_member
        JOIN `tabBook` b            ON b.name  = bt.book
        WHERE bt.transaction_type = 'Issue'
          AND bt.docstatus = 1
          AND bt.due_date < CURDATE()
          {conditions}
          AND NOT EXISTS (
              SELECT 1 FROM `tabBook Transaction` ret
              WHERE ret.transaction_type = 'Return'
                AND ret.library_member = bt.library_member
                AND ret.book = bt.book
                AND ret.docstatus = 1
          )
        ORDER BY bt.due_date ASC
        """,
        filters,
        as_dict=True,
    )

    for row in rows:
        row["fine_accrued"] = (row["overdue_days"] or 0) * fine_per_day

    return rows

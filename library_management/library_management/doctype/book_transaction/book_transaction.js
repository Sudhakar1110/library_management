frappe.ui.form.on("Book Transaction", {
    refresh(frm) {
        // Status badge
        if (!frm.is_new()) {
            if (frm.doc.transaction_type === "Issue" && frm.doc.docstatus === 1) {
                const dueDate = frm.doc.due_date;
                const today = frappe.datetime.get_today();
                if (dueDate && dueDate < today) {
                    frm.dashboard.add_indicator("Overdue", "red");
                } else {
                    frm.dashboard.add_indicator("Issued", "blue");
                }
            }
            if (frm.doc.transaction_type === "Return" && frm.doc.docstatus === 1) {
                frm.dashboard.add_indicator("Returned", "green");
            }
        }

        // Show fine info
        if (frm.doc.fine_amount > 0) {
            frm.dashboard.add_indicator(
                `Fine: ${format_currency(frm.doc.fine_amount)} ${frm.doc.fine_paid ? "(Paid)" : "(Unpaid)"}`,
                frm.doc.fine_paid ? "green" : "red"
            );
        }

        // Quick Return button in list of issues
        if (
            frm.doc.transaction_type === "Issue" &&
            frm.doc.docstatus === 1 &&
            frappe.user.has_role("Librarian")
        ) {
            frm.add_custom_button("Create Return", () => {
                frappe.new_doc("Book Transaction", {
                    transaction_type: "Return",
                    library_member: frm.doc.library_member,
                    book: frm.doc.book,
                    return_date: frappe.datetime.get_today(),
                });
            });
        }
    },

    transaction_type(frm) {
        // Auto set today's date
        if (frm.doc.transaction_type === "Issue") {
            frm.set_value("issue_date", frappe.datetime.get_today());
        } else if (frm.doc.transaction_type === "Return") {
            frm.set_value("return_date", frappe.datetime.get_today());
        }
    },

    library_member(frm) {
        if (frm.doc.library_member) {
            frappe.db.get_value("Library Member", frm.doc.library_member, "status", (r) => {
                if (r && r.status !== "Active") {
                    frappe.msgprint({
                        title: "Member Status Warning",
                        message: `This member's status is <b>${r.status}</b>. They may not be able to borrow books.`,
                        indicator: "orange",
                    });
                }
            });
        }
    },
});

function format_currency(amount) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: frappe.boot.sysdefaults.currency || "INR",
        minimumFractionDigits: 2,
    }).format(amount);
}

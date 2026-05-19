frappe.ui.form.on("Library Member", {
    refresh(frm) {
        if (!frm.is_new()) {
            const status = frm.doc.status;
            const colorMap = { Active: "green", Expired: "red", Suspended: "orange" };
            frm.dashboard.add_indicator(status, colorMap[status] || "gray");

            // Quick action: View transactions
            frm.add_custom_button("View Transactions", () => {
                frappe.set_route("List", "Book Transaction", {
                    library_member: frm.doc.name,
                });
            }, "Actions");

            // Renew membership button
            frm.add_custom_button("Renew Membership", () => {
                frappe.prompt(
                    [
                        {
                            fieldname: "end_date",
                            fieldtype: "Date",
                            label: "New End Date",
                            reqd: 1,
                        },
                    ],
                    ({ end_date }) => {
                        frm.set_value("membership_end_date", end_date);
                        frm.save();
                    },
                    "Renew Membership"
                );
            }, "Actions");
        }

        // Auto-set start date on new
        if (frm.is_new() && !frm.doc.membership_start_date) {
            frm.set_value("membership_start_date", frappe.datetime.get_today());
        }
    },
});

frappe.ui.form.on("Book", {
    refresh(frm) {
        // Show availability badge
        if (!frm.is_new()) {
            const avail = frm.doc.available_copies || 0;
            const total = frm.doc.total_copies || 0;
            const color = avail === 0 ? "red" : avail < total ? "orange" : "green";
            frm.dashboard.add_indicator(
                `${avail} / ${total} Available`,
                color
            );
        }
    },

    total_copies(frm) {
        // When adding copies for the first time
        if (frm.is_new()) {
            frm.set_value("available_copies", frm.doc.total_copies);
        }
    },
});

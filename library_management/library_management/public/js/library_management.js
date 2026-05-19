/**
 * Library Management — Global Desk JS
 * Loaded on all desk pages via hooks.py app_include_js
 */

frappe.provide("library_management");

library_management.utils = {
    /**
     * Open a quick-issue dialog from anywhere in the desk.
     */
    quick_issue() {
        const d = new frappe.ui.Dialog({
            title: "Quick Issue Book",
            fields: [
                {
                    fieldname: "library_member",
                    fieldtype: "Link",
                    label: "Member",
                    options: "Library Member",
                    reqd: 1,
                    filters: { status: "Active" },
                },
                {
                    fieldname: "book",
                    fieldtype: "Link",
                    label: "Book",
                    options: "Book",
                    reqd: 1,
                    get_query() {
                        return { filters: { available_copies: [">", 0] } };
                    },
                },
            ],
            primary_action_label: "Issue",
            primary_action({ library_member, book }) {
                frappe.call({
                    method: "library_management.api.api.issue_book",
                    args: {
                        member_id: library_member,
                        isbn: null, // resolved server-side via book name
                        book_name: book,
                    },
                    callback({ message }) {
                        frappe.show_alert({
                            message: message.message,
                            indicator: "green",
                        });
                        d.hide();
                    },
                });
            },
        });
        d.show();
    },
};

// Add shortcut to the global search bar
$(document).on("app_ready", () => {
    frappe.search.utils.make_function_searchable(
        library_management.utils.quick_issue,
        "Quick Issue Book"
    );
});

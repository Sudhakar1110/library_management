app_name = "library_management"
app_title = "Library Management"
app_publisher = "Your Name"
app_description = "Library Management System for ERPNext v15"
app_email = "your@email.com"
app_license = "MIT"
app_version = "1.0.0"

# Required Apps
required_apps = ["frappe"]

# DocTypes
# --------
# List of doctype json to be ignore from migration
# ignore_migrate_on_inactive_children = True

# Include js, css files in header of desk.html
# app_include_css = "/assets/library_management/css/library_management.css"
app_include_js = "/assets/library_management/js/library_management.js"

# Include js, css files in header of web template
# web_include_css = "/assets/library_management/css/library_management.css"
# web_include_js = "/assets/library_management/js/library_management.js"

# Home Pages
# ----------
# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Fixtures
# --------
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Library Management"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Library Management"]]},
    "Library Settings",
]

# Document Events
# ---------------
doc_events = {
    "Book Transaction": {
        "on_submit": "library_management.doctype.book_transaction.book_transaction.on_submit",
        "on_cancel": "library_management.doctype.book_transaction.book_transaction.on_cancel",
    }
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "daily": [
        "library_management.tasks.send_overdue_reminders",
    ],
    "hourly": [],
    "weekly": [],
    "monthly": [],
}

# Testing
# -------
before_tests = "library_management.install.before_tests"

# Permissions
# -----------
# Permissions evaluated in scripted ways
# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes
# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Override standard doctype form javascript
# override_doctype_js = {
#   "Work Order" : "public/js/work_order.js"
# }

# Override Whitelisted Methods
# ----------------------------
# override_whitelisted_methods = {
# 	"frappe.client.get_list": "library_management.api.get_list"
# }

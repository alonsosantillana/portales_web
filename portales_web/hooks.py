app_name = "portales_web"
app_title = "Portales Web"
app_publisher = "Portales Web"
app_description = "Aplicación Frappe para la gestión de portales web."
app_email = "desarrollo@example.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

portal_menu_items = [
	{
		"title": "Registrar Factura",
		"route": "/registrar-factura",
		"role": "Supplier",
	},
	{
		"title": "Facturar recepción",
		"route": "/registrar-factura-recepcion",
		"role": "Supplier",
	},
]

website_route_rules = [
	{"from_route": "/registrar-factura", "to_route": "registrar_factura"},
	{
		"from_route": "/registrar-factura-recepcion",
		"to_route": "registrar_factura_recepcion",
	},
]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "portales_web",
# 		"logo": "/assets/portales_web/logo.png",
# 		"title": "Portales Web",
# 		"route": "/portales_web",
# 		"has_permission": "portales_web.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/portales_web/css/portales_web.css"
# app_include_js = "/assets/portales_web/js/portales_web.js"

# include js, css files in header of web template
# web_include_css = "/assets/portales_web/css/portales_web.css"
# web_include_js = "/assets/portales_web/js/portales_web.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "portales_web/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "portales_web/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "portales_web.utils.jinja_methods",
# 	"filters": "portales_web.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "portales_web.install.before_install"
# after_install = "portales_web.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "portales_web.uninstall.before_uninstall"
# after_uninstall = "portales_web.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "portales_web.utils.before_app_install"
# after_app_install = "portales_web.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "portales_web.utils.before_app_uninstall"
# after_app_uninstall = "portales_web.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "portales_web.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Purchase Invoice": {
		"on_submit": "portales_web.portales_web.doctype.supplier_invoice_submission.supplier_invoice_submission.sync_purchase_invoice_status",
		"on_cancel": "portales_web.portales_web.doctype.supplier_invoice_submission.supplier_invoice_submission.sync_purchase_invoice_status",
		"on_trash": "portales_web.portales_web.doctype.supplier_invoice_submission.supplier_invoice_submission.sync_purchase_invoice_status",
	}
}

has_website_permission = {
	"Supplier Invoice Submission": "portales_web.portales_web.doctype.supplier_invoice_submission.supplier_invoice_submission.has_website_permission",
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"portales_web.tasks.all"
# 	],
# 	"daily": [
# 		"portales_web.tasks.daily"
# 	],
# 	"hourly": [
# 		"portales_web.tasks.hourly"
# 	],
# 	"weekly": [
# 		"portales_web.tasks.weekly"
# 	],
# 	"monthly": [
# 		"portales_web.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "portales_web.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "portales_web.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "portales_web.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["portales_web.utils.before_request"]
# after_request = ["portales_web.utils.after_request"]

# Job Events
# ----------
# before_job = ["portales_web.utils.before_job"]
# after_job = ["portales_web.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"portales_web.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

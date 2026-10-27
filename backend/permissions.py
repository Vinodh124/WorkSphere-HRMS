from auth import get_current_user, require_roles

# Any authenticated role
require_authenticated = get_current_user

# HR and ADMIN access
require_hr_or_admin = require_roles("HR", "ADMIN")

# ADMIN-only access
require_admin = require_roles("ADMIN")

# EMPLOYEE self-service access
require_employee = require_roles("EMPLOYEE")
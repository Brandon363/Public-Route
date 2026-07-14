# ---------------------------------------------------------------------------
# Role string constants — ServiceFlow AI role set.
# These are the canonical string values stored in the User.role column.
# ---------------------------------------------------------------------------

ROLE_CITIZEN         = "citizen"
ROLE_INTAKE_OFFICER  = "intake_officer"
ROLE_DISPATCHER      = "dispatcher"
ROLE_FIELD_TEAM      = "field_team"
ROLE_SUPERVISOR      = "supervisor"
ROLE_ANALYST         = "analyst"
ROLE_MANAGER         = "manager"
ROLE_ADMINISTRATOR   = "administrator"
ROLE_AUDITOR         = "auditor"


# ---------------------------------------------------------------------------
# Permission group constants.
# Each constant is a list of role strings authorised to perform the action.
# Use directly with RoleChecker in controllers.
# ---------------------------------------------------------------------------

# Full platform administration: users, roles, reference data, integrations.
CAN_MANAGE_USERS = [ROLE_ADMINISTRATOR]

# Create and validate intake submissions.
CAN_CREATE_SUBMISSIONS = [
    ROLE_CITIZEN, ROLE_INTAKE_OFFICER, ROLE_DISPATCHER,
]

# Read and process intake queue.
CAN_PROCESS_INTAKE = [ROLE_INTAKE_OFFICER, ROLE_DISPATCHER, ROLE_ADMINISTRATOR]

# Route cases to queues and merge duplicates.
CAN_ROUTE_CASES = [ROLE_DISPATCHER, ROLE_SUPERVISOR, ROLE_ADMINISTRATOR]

# View and update assigned field work.
CAN_UPDATE_ASSIGNMENTS = [ROLE_FIELD_TEAM, ROLE_SUPERVISOR, ROLE_ADMINISTRATOR]

# Manage SLA, escalations and queue operations.
CAN_MANAGE_QUEUE = [ROLE_SUPERVISOR, ROLE_ADMINISTRATOR]

# Access operational analytics and governed datasets.
CAN_VIEW_ANALYTICS = [
    ROLE_ANALYST, ROLE_MANAGER, ROLE_SUPERVISOR, ROLE_ADMINISTRATOR,
]

# Read case records — broader than CAN_ROUTE_CASES since intake officers,
# analysts and managers also need read access without routing rights.
CAN_VIEW_CASES = list(dict.fromkeys([
    ROLE_INTAKE_OFFICER, ROLE_DISPATCHER, ROLE_SUPERVISOR,
    ROLE_ANALYST, ROLE_MANAGER, ROLE_ADMINISTRATOR,
]))

# Approve, reject or modify AI recommendations.
CAN_APPROVE_RECOMMENDATIONS = [ROLE_MANAGER, ROLE_ADMINISTRATOR]

# View immutable audit and model evidence — no operational edits.
CAN_VIEW_AUDIT = [ROLE_AUDITOR, ROLE_ADMINISTRATOR]

# Configure reference data (districts, org units, queues, teams).
CAN_MANAGE_REFERENCE_DATA = [ROLE_ADMINISTRATOR]

# Run approved forecasting and optimisation pipelines.
CAN_RUN_MODELS = [ROLE_ANALYST, ROLE_ADMINISTRATOR]

# Generate management briefings and export data.
CAN_GENERATE_REPORTS = [ROLE_MANAGER, ROLE_ANALYST, ROLE_ADMINISTRATOR]


# ---------------------------------------------------------------------------
# Convenience collections.
# ---------------------------------------------------------------------------

# All valid platform roles.
ALL_ROLES = [
    ROLE_CITIZEN,
    ROLE_INTAKE_OFFICER,
    ROLE_DISPATCHER,
    ROLE_FIELD_TEAM,
    ROLE_SUPERVISOR,
    ROLE_ANALYST,
    ROLE_MANAGER,
    ROLE_ADMINISTRATOR,
    ROLE_AUDITOR,
]

# Internal staff roles (not citizen-facing portal accounts).
INTERNAL_ROLES = [
    ROLE_INTAKE_OFFICER,
    ROLE_DISPATCHER,
    ROLE_FIELD_TEAM,
    ROLE_SUPERVISOR,
    ROLE_ANALYST,
    ROLE_MANAGER,
    ROLE_ADMINISTRATOR,
    ROLE_AUDITOR,
]

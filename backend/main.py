from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from Config.database import Base, engine
from Config.middleware_and_cors import MyMiddleware
from starlette.middleware.cors import CORSMiddleware

from Controller import auth_controller, user_controller, whatsapp_controller
from Controller import (
    district_controller,
    organisation_unit_controller,
    queue_controller,
    resource_team_controller,
)
from Controller import intake_controller, case_controller, audit_event_controller

# ---------------------------------------------------------------------------
# Import every entity so SQLAlchemy's mapper registry is fully populated
# before Base.metadata.create_all runs. Order matters:
# - User must come first (referenced by Approval and AuditEvent FKs).
# - District before Submission, Case, ResourceTeam, Forecast.
# - OrganisationUnit before Queue.
# - Queue before Case.
# - Submission before Case, Document, Notification.
# - Case and IncidentCluster before Assignment.
# - ModelVersion before Forecast and Recommendation.
# - Forecast before Recommendation.
# - Recommendation before Approval.
# ---------------------------------------------------------------------------
from Entity.user_entity              import User                 # noqa: F401
from Entity.district_entity          import District             # noqa: F401
from Entity.organisation_unit_entity import OrganisationUnit     # noqa: F401
from Entity.queue_entity             import Queue                # noqa: F401
from Entity.resource_team_entity     import ResourceTeam         # noqa: F401
from Entity.citizen_contact_entity   import CitizenContact       # noqa: F401
from Entity.submission_entity        import Submission           # noqa: F401
from Entity.document_entity          import Document             # noqa: F401
from Entity.case_entity              import Case                 # noqa: F401
from Entity.incident_cluster_entity  import IncidentCluster      # noqa: F401
from Entity.assignment_entity        import Assignment           # noqa: F401
from Entity.notification_entity      import Notification         # noqa: F401
from Entity.model_version_entity     import ModelVersion         # noqa: F401
from Entity.forecast_entity          import Forecast             # noqa: F401
from Entity.recommendation_entity    import Recommendation       # noqa: F401
from Entity.approval_entity          import Approval             # noqa: F401
from Entity.audit_event_entity       import AuditEvent           # noqa: F401
from Entity.whatsapp_session_entity  import WhatsAppSession      # noqa: F401

from Utils.seeder import seed_admin_user, seed_reference_data, seed_role_accounts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Create all database tables that do not yet exist.
    Base.metadata.create_all(bind=engine)
    
    # Run auto-migrations to ensure contact and translation columns exist
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS contact_email TEXT;"))
        conn.execute(text("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS contact_phone TEXT;"))
        conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS english_description TEXT;"))
        conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS contact_email TEXT;"))
        conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS contact_phone TEXT;"))
    # Seed the default administrator account on first run.
    seed_admin_user()
    # Seed starter districts/organisation units/queues so the intake →
    # classification → routing pipeline is demoable with no manual setup.
    seed_reference_data()
    # Seed one demo account per role for development / QA use.
    seed_role_accounts()

    yield

    # --- Shutdown (extend here if teardown is needed) ---


app = FastAPI(
    title="ServiceFlow AI API",
    version="1.0.0",
    description=(
        "Inclusive citizen intake, intelligent case processing "
        "and predictive public-service operations."
    ),
    lifespan=lifespan,
)

api_router = APIRouter(prefix="/api/v1")

# ── Auth & User management ────────────────────────────────────────────────
api_router.include_router(auth_controller.router)
api_router.include_router(user_controller.router)

# ── Reference data ────────────────────────────────────────────────────────
api_router.include_router(district_controller.router)
api_router.include_router(organisation_unit_controller.router)
api_router.include_router(queue_controller.router)
api_router.include_router(resource_team_controller.router)

# ── Intake, case pipeline & audit ─────────────────────────────────────────
api_router.include_router(intake_controller.router)
api_router.include_router(case_controller.router)
api_router.include_router(audit_event_controller.router)
api_router.include_router(whatsapp_controller.router)

# Additional feature routers will be registered here as they are built.


@api_router.get("/", tags=["Health"])
def read_root():
    return {"message": "ServiceFlow AI — server is running."}


app.include_router(api_router)

app.add_middleware(MyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8015, reload=True)
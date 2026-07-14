from sqlalchemy.orm import Session
from loguru import logger

from Config.database import SessionLocal
from Entity.user_entity import User
from Entity.district_entity import District
from Entity.organisation_unit_entity import OrganisationUnit
from Entity.queue_entity import Queue
from Repository.district_repository import DistrictRepository
from Repository.organisation_unit_repository import OrganisationUnitRepository
from Repository.queue_repository import QueueRepository
from Utils.security import get_password_hash
from Utils.permissions import (
    ROLE_CITIZEN,
    ROLE_INTAKE_OFFICER,
    ROLE_DISPATCHER,
    ROLE_FIELD_TEAM,
    ROLE_SUPERVISOR,
    ROLE_ANALYST,
    ROLE_MANAGER,
    ROLE_ADMINISTRATOR,
    ROLE_AUDITOR,
)
from Utils.service_categories import CATEGORY_KEYWORDS

# ---------------------------------------------------------------------------
# Default administrator credentials.
# Change these (or remove this seeder) before going to production.
# ---------------------------------------------------------------------------

_SUPER_ADMIN_EMAIL    = "super.admin@serviceflow.ai"
_SUPER_ADMIN_PASSWORD = "Demo@Admin"


# ---------------------------------------------------------------------------
# One demo account per role — for development / QA use only.
# Email pattern : <role>@demo.serviceflow.ai
# Password      : Demo@<Role> (e.g. Demo@Citizen, Demo@Supervisor)
# ---------------------------------------------------------------------------

_ROLE_SEED_ACCOUNTS = [
    {
        "role":      ROLE_CITIZEN,
        "email":     "citizen@demo.serviceflow.ai",
        "full_name": "Demo Citizen",
        "password":  "Demo@Citizen",
    },
    {
        "role":      ROLE_INTAKE_OFFICER,
        "email":     "intake.officer@demo.serviceflow.ai",
        "full_name": "Demo Intake Officer",
        "password":  "Demo@IntakeOfficer",
    },
    {
        "role":      ROLE_DISPATCHER,
        "email":     "dispatcher@demo.serviceflow.ai",
        "full_name": "Demo Dispatcher",
        "password":  "Demo@Dispatcher",
    },
    {
        "role":      ROLE_FIELD_TEAM,
        "email":     "field.team@demo.serviceflow.ai",
        "full_name": "Demo Field Team Member",
        "password":  "Demo@FieldTeam",
    },
    {
        "role":      ROLE_SUPERVISOR,
        "email":     "supervisor@demo.serviceflow.ai",
        "full_name": "Demo Supervisor",
        "password":  "Demo@Supervisor",
    },
    {
        "role":      ROLE_ANALYST,
        "email":     "analyst@demo.serviceflow.ai",
        "full_name": "Demo Analyst",
        "password":  "Demo@Analyst",
    },
    {
        "role":      ROLE_MANAGER,
        "email":     "manager@demo.serviceflow.ai",
        "full_name": "Demo Manager",
        "password":  "Demo@Manager",
    },
    {
        "role":      ROLE_ADMINISTRATOR,
        "email":     "admin@demo.serviceflow.ai",
        "full_name": "Demo Administrator",
        "password":  "Demo@Administrator",
    },
    {
        "role":      ROLE_AUDITOR,
        "email":     "auditor@demo.serviceflow.ai",
        "full_name": "Demo Auditor",
        "password":  "Demo@Auditor",
    },
]


def seed_admin_user() -> None:
    """
    Seed one default administrator user if no matching user exists yet.

    Idempotent and self-healing: if the account already exists but was
    seeded with a stale/incorrect role (e.g. an older "super_admin" value
    that Utils/permissions.py never recognised as an admin role), the role
    is corrected in place rather than left broken. Safe to call on every
    startup.
    """
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(
            User.email == _SUPER_ADMIN_EMAIL
        ).first()

        if existing is not None:
            if existing.role != ROLE_ADMINISTRATOR:
                logger.warning(
                    f"Seeded admin had role '{existing.role}', which "
                    f"Utils/permissions.py does not recognise as an admin "
                    f"role — correcting to '{ROLE_ADMINISTRATOR}'."
                )
                existing.role = ROLE_ADMINISTRATOR
                db.commit()
            else:
                logger.info("Admin user already present. Skipping seed.")
            return

        logger.info("Seeding default administrator user...")

        db_user = User(
            email=_SUPER_ADMIN_EMAIL,
            hashed_password=get_password_hash(_SUPER_ADMIN_PASSWORD),
            role=ROLE_ADMINISTRATOR,
        )
        db.add(db_user)
        db.commit()

        logger.info(f"  Created administrator: {_SUPER_ADMIN_EMAIL}")
        logger.info("Admin user seeded successfully.")

    except Exception as exc:
        db.rollback()
        logger.error(f"Admin seed failed and was rolled back: {exc}")
        raise

    finally:
        db.close()


def seed_role_accounts() -> None:
    """
    Seed one demo user account for every platform role.

    Idempotent: accounts that already exist (matched by e-mail) are left
    untouched. Only the role field is corrected if it drifted from the
    expected value (same self-healing logic as ``seed_admin_user``).

    **Development / QA only** — remove or gate behind an env-flag before
    going to production.
    """
    db: Session = SessionLocal()
    try:
        created = 0
        for spec in _ROLE_SEED_ACCOUNTS:
            existing = db.query(User).filter(User.email == spec["email"]).first()

            if existing is not None:
                # Self-heal role drift.
                if existing.role != spec["role"]:
                    logger.warning(
                        f"Demo account '{spec['email']}' had role "
                        f"'{existing.role}' — correcting to '{spec['role']}'."
                    )
                    existing.role = spec["role"]
                    db.commit()
                continue

            db.add(User(
                email=spec["email"],
                full_name=spec["full_name"],
                hashed_password=get_password_hash(spec["password"]),
                role=spec["role"],
            ))
            created += 1

        if created:
            db.commit()
            logger.info(f"Seeded {created} demo role account(s).")
        else:
            logger.info("Demo role accounts already present. Skipping seed.")

    except Exception as exc:
        db.rollback()
        logger.error(f"Role account seed failed and was rolled back: {exc}")
        raise

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Minimal reference data so the intake → classification → routing pipeline
# is demoable immediately after a fresh startup, with no manual setup.
#
# This is a small illustrative starter set, not authoritative institutional
# geography or an official department directory — replace/extend it once a
# real pilot institution's reference data is onboarded (DR-008).
# ---------------------------------------------------------------------------

_STARTER_DISTRICTS = [
    {"name": "Harare Central", "province": "Harare", "settlement_type": "urban"},
    {"name": "Bulawayo Central", "province": "Bulawayo", "settlement_type": "urban"},
    {"name": "Chitungwiza", "province": "Harare", "settlement_type": "urban"},
    {"name": "Epworth", "province": "Harare", "settlement_type": "peri_urban"},
    {"name": "Mutare", "province": "Manicaland", "settlement_type": "urban"},
    {"name": "Gweru", "province": "Midlands", "settlement_type": "urban"},
]

# One responsible unit per classification category (Utils/service_categories.py).
# jurisdiction is left empty ([]) on purpose — routing_service.py treats an
# empty jurisdiction as "covers every district" so routing works regardless
# of which starter district a demo submission uses.
_STARTER_UNIT_NAMES = {
    "water_sanitation": "Water & Sanitation Department",
    "roads_infrastructure": "Roads & Infrastructure Department",
    "electricity_power": "Electricity & Power Utility",
    "waste_management": "Waste Management Department",
    "health_services": "Health Services Department",
    "security_safety": "Security & Safety Department",
}


def seed_reference_data() -> None:
    """
    Seed starter districts, organisation units and queues.

    Idempotent per item (checked by unique name), safe to call on every
    startup — existing rows are left untouched, only missing ones are added.
    """
    db: Session = SessionLocal()
    try:
        _seed_districts(db)
        _seed_service_units_and_queues(db)
    except Exception as exc:
        db.rollback()
        logger.error(f"Reference data seed failed and was rolled back: {exc}")
        raise
    finally:
        db.close()


def _seed_districts(db: Session) -> None:
    repository = DistrictRepository(db)
    created = 0
    for entry in _STARTER_DISTRICTS:
        if repository.get_by_name(entry["name"]) is not None:
            continue
        repository.create(District(**entry))
        created += 1
    if created:
        logger.info(f"Seeded {created} starter district(s).")


def _seed_service_units_and_queues(db: Session) -> None:
    unit_repository = OrganisationUnitRepository(db)
    queue_repository = QueueRepository(db)
    created_units = 0
    created_queues = 0

    for category in CATEGORY_KEYWORDS:
        unit_name = _STARTER_UNIT_NAMES.get(category)
        if unit_name is None:
            continue

        unit = unit_repository.get_by_name(unit_name)
        if unit is None:
            unit = unit_repository.create(OrganisationUnit(
                name=unit_name,
                jurisdiction=[],
                service_categories=[category],
            ))
            created_units += 1

        if not queue_repository.get_by_unit_id(unit.id):
            queue_repository.create(Queue(
                unit_id=unit.id,
                name=f"{unit_name} - Intake Queue",
                capacity=100,
            ))
            created_queues += 1

    if created_units or created_queues:
        logger.info(
            f"Seeded {created_units} organisation unit(s) and "
            f"{created_queues} queue(s)."
        )

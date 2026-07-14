from typing import Optional
from sqlalchemy.orm import Session
from Repository.organisation_unit_repository import OrganisationUnitRepository
from Repository.queue_repository import QueueRepository
from Entity.queue_entity import Queue


def recommend_queue(db: Session, category: str, district_id: Optional[int]) -> Optional[Queue]:
    """
    Recommend the responsible queue for a case (FR-009).

    jurisdiction/service_categories are plain JSON columns (not JSONB), so
    there is no SQL containment query available — filter in Python over the
    active-units list, matching the precedent set by
    OrganisationUnitRepository.get_active().

    An empty jurisdiction list means "all districts" for that unit. Returns
    None if no unit/queue match is found — the caller leaves the case for
    manual routing rather than guessing.
    """
    unit_repo = OrganisationUnitRepository(db)
    queue_repo = QueueRepository(db)

    matching_units = [
        unit
        for unit in unit_repo.get_active()
        if category in (unit.service_categories or [])
        and (not unit.jurisdiction or district_id in (unit.jurisdiction or []))
    ]

    for unit in matching_units:
        active_queues = [
            queue for queue in queue_repo.get_by_unit_id(unit.id) if queue.is_active
        ]
        if active_queues:
            return active_queues[0]

    return None

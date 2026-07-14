from sqlalchemy.orm import Session
from Repository.queue_repository import QueueRepository
from Repository.organisation_unit_repository import OrganisationUnitRepository
from Schema.queue_schema import QueueCreate, QueueUpdate
from Entity.queue_entity import Queue


class QueueService:
    """
    Business logic for the Queue reference data domain.
    No FastAPI imports — raises ValueError for all rule violations.

    A Queue must belong to an active OrganisationUnit. This cross-entity
    check is the service layer's responsibility.
    """

    def __init__(self, db: Session):
        self.repository = QueueRepository(db)
        self.unit_repository = OrganisationUnitRepository(db)

    def _assert_unit_exists_and_active(self, unit_id: int) -> None:
        unit = self.unit_repository.get_by_id(unit_id)
        if unit is None:
            raise ValueError(f"Organisation unit with ID {unit_id} not found.")
        if not unit.is_active:
            raise ValueError(
                f"Organisation unit with ID {unit_id} is inactive. "
                "Queues may only be created for active units."
            )

    def create_queue(self, data: QueueCreate) -> Queue:
        """
        Create a new queue for an active organisation unit.
        Queue names must be unique within the same unit.
        """
        self._assert_unit_exists_and_active(data.unit_id)

        # Enforce unique queue name per unit
        existing_queues = self.repository.get_by_unit_id(data.unit_id)
        if any(q.name == data.name for q in existing_queues):
            raise ValueError(
                f"A queue named '{data.name}' already exists for unit ID {data.unit_id}."
            )

        queue = Queue(
            unit_id=data.unit_id,
            name=data.name,
            priority_rules=data.priority_rules or {},
            capacity=data.capacity,
            is_active=data.is_active,
        )
        return self.repository.create(queue)

    def get_queue(self, queue_id: int) -> Queue:
        queue = self.repository.get_by_id(queue_id)
        if queue is None:
            raise ValueError(f"Queue with ID {queue_id} not found.")
        return queue

    def get_all_queues(self, skip: int = 0, limit: int = 100) -> list[Queue]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get_active_queues(self) -> list[Queue]:
        return self.repository.get_active()

    def get_queues_by_unit(self, unit_id: int) -> list[Queue]:
        return self.repository.get_by_unit_id(unit_id)

    def update_queue(self, queue_id: int, data: QueueUpdate) -> Queue:
        queue = self.repository.get_by_id(queue_id)
        if queue is None:
            raise ValueError(f"Queue with ID {queue_id} not found.")

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing_queues = self.repository.get_by_unit_id(queue.unit_id)
            if any(
                q.name == update_data["name"] and q.id != queue_id
                for q in existing_queues
            ):
                raise ValueError(
                    f"A queue named '{update_data['name']}' already exists "
                    f"for unit ID {queue.unit_id}."
                )

        return self.repository.update(queue, update_data)

    def deactivate_queue(self, queue_id: int) -> Queue:
        """Soft-delete: marks queue inactive without removing it."""
        queue = self.repository.get_by_id(queue_id)
        if queue is None:
            raise ValueError(f"Queue with ID {queue_id} not found.")
        return self.repository.update(queue, {"is_active": False})

    def delete_queue(self, queue_id: int) -> None:
        queue = self.repository.get_by_id(queue_id)
        if queue is None:
            raise ValueError(f"Queue with ID {queue_id} not found.")
        self.repository.delete(queue)

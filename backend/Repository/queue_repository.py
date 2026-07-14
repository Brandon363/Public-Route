from sqlalchemy.orm import Session
from Entity.queue_entity import Queue


class QueueRepository:
    """
    Data access layer for the Queue reference table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, queue_id: int) -> Queue | None:
        return self.db.query(Queue).filter(Queue.id == queue_id).first()

    def get_by_unit_id(self, unit_id: int) -> list[Queue]:
        return self.db.query(Queue).filter(Queue.unit_id == unit_id).all()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Queue]:
        return self.db.query(Queue).offset(skip).limit(limit).all()

    def get_active(self) -> list[Queue]:
        return (
            self.db.query(Queue)
            .filter(Queue.is_active == True)  # noqa: E712
            .all()
        )

    def create(self, queue: Queue) -> Queue:
        self.db.add(queue)
        self.db.commit()
        self.db.refresh(queue)
        return queue

    def update(self, queue: Queue, update_data: dict) -> Queue:
        for key, value in update_data.items():
            setattr(queue, key, value)
        self.db.commit()
        self.db.refresh(queue)
        return queue

    def delete(self, queue: Queue) -> None:
        self.db.delete(queue)
        self.db.commit()

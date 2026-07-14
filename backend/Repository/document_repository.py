from uuid import UUID
from sqlalchemy.orm import Session
from Entity.document_entity import Document


class DocumentRepository:
    """
    Data access layer for the Document (uploaded file) table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: UUID) -> Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_by_submission(self, submission_id: UUID) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.submission_id == submission_id)
            .all()
        )

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: Document, update_data: dict) -> Document:
        for key, value in update_data.items():
            setattr(document, key, value)
        self.db.commit()
        self.db.refresh(document)
        return document

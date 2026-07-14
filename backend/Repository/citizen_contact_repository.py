from sqlalchemy.orm import Session
from Entity.citizen_contact_entity import CitizenContact


class CitizenContactRepository:
    """
    Data access layer for the PII-separated CitizenContact table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, contact_id: int) -> CitizenContact | None:
        return self.db.query(CitizenContact).filter(CitizenContact.id == contact_id).first()

    def get_by_token(self, token: str) -> CitizenContact | None:
        return (
            self.db.query(CitizenContact)
            .filter(CitizenContact.encrypted_phone == token)
            .first()
        )

    def create(self, contact: CitizenContact) -> CitizenContact:
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def update(self, contact: CitizenContact, update_data: dict) -> CitizenContact:
        for key, value in update_data.items():
            setattr(contact, key, value)
        self.db.commit()
        self.db.refresh(contact)
        return contact

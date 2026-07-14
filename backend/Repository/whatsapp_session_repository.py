from sqlalchemy.orm import Session
from Entity.whatsapp_session_entity import WhatsAppSession

class WhatsAppSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_phone(self, phone_number: str) -> WhatsAppSession | None:
        return self.db.query(WhatsAppSession).filter(WhatsAppSession.phone_number == phone_number).first()

    def create_or_update(self, phone_number: str, description: str, location: str) -> WhatsAppSession:
        session = self.get_by_phone(phone_number)
        if session:
            session.accumulated_description = description
            session.accumulated_location = location
        else:
            session = WhatsAppSession(
                phone_number=phone_number,
                accumulated_description=description,
                accumulated_location=location
            )
            self.db.add(session)
        
        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_by_phone(self, phone_number: str) -> None:
        session = self.get_by_phone(phone_number)
        if session:
            self.db.delete(session)
            self.db.commit()

from sqlalchemy import Column, Integer, String, DateTime
from Config.database import Base, TimestampMixin

class WhatsAppSession(Base, TimestampMixin):
    """
    Tracks state of the WhatsApp chatbot conversation per user (phone number).
    """
    __tablename__ = "whatsapp_sessions"

    id                      = Column(Integer, primary_key=True, index=True)
    phone_number            = Column(String, unique=True, index=True, nullable=False)
    accumulated_description = Column(String, nullable=True)
    accumulated_location    = Column(String, nullable=True)

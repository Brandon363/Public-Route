import uuid
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import MalwareStatusEnum


class Document(Base, TimestampMixin):
    """
    Uploaded file record — PDFs, images, scanned reports.

    Binary content is NEVER stored here; only a reference to the encrypted
    object store (storage_ref). OCR text and structured field extraction
    results are written back by the processing pipeline.
    Malware scanning must complete before extraction begins.
    """
    __tablename__ = "documents"

    id              = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    submission_id   = Column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False
    )
    file_hash       = Column(String, nullable=True)         # SHA-256 of original file
    mime_type       = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    storage_ref     = Column(String, nullable=True)         # encrypted object store path
    ocr_text        = Column(Text, nullable=True)
    extraction_json = Column(JSON, nullable=True, default=dict)
    malware_status  = Column(
        String, nullable=False, default=MalwareStatusEnum.PENDING
    )

    # Relationships
    submission      = relationship("Submission", back_populates="documents")

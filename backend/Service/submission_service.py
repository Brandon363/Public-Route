from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from Repository.submission_repository import SubmissionRepository
from Service.citizen_contact_service import CitizenContactService
from Service.audit_event_service import AuditEventService
from Entity.submission_entity import Submission
from Schema.submission_schema import SubmissionCreate


class SubmissionService:
    """
    Business logic for the intake envelope (architecture §3 canonical schema).
    No FastAPI imports — raises ValueError for all rule violations.
    """

    def __init__(self, db: Session):
        self.repository = SubmissionRepository(db)
        self.citizen_contact_service = CitizenContactService(db)
        self.audit_service = AuditEventService(db)

    def create_submission(
        self,
        data: SubmissionCreate,
        actor_user_id: Optional[int] = None,
        actor_channel: Optional[str] = None,
    ) -> Submission:
        if not data.service_description or not data.service_description.strip():
            raise ValueError("service_description is required.")

        # received_at is always server-set (server UTC), never trusted from
        # the client payload, per the architecture doc's canonical schema.
        received_at = datetime.now(timezone.utc)

        contact = self.citizen_contact_service.find_or_create(
            raw_identifier=data.citizen_contact_token,
            preferred_channel=data.channel.value,
            language_code=data.language_code,
        )
        contact_token = contact.encrypted_phone if contact else None

        submission = Submission(
            channel=data.channel.value,
            received_at=received_at,
            service_description=data.service_description,
            location_text=data.location_text,
            language_code=data.language_code,
            language_confidence=data.language_confidence,
            consent_status=data.consent_status.value,
            citizen_contact_token=contact_token,
            transcript=data.transcript,
            raw_text_ref=data.raw_text_ref,
            attachment_refs=data.attachment_refs or [],
            accessibility_preferences=data.accessibility_preferences or {},
            source_metadata=data.source_metadata or {},
            citizen_contact_id=contact.id if contact else data.citizen_contact_id,
            district_id=data.district_id,
            submitter_user_id=actor_user_id,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
        )
        submission = self.repository.create(submission)

        self.audit_service.log(
            action="submission.created",
            object_type="submission",
            object_id=str(submission.id),
            actor_user_id=actor_user_id,
            actor_channel=actor_channel or data.channel.value,
            after={
                "channel": submission.channel,
                "consent_status": submission.consent_status,
                "district_id": submission.district_id,
                "citizen_contact_id": submission.citizen_contact_id,
            },
        )

        return submission

    def get_submission(self, submission_id) -> Submission:
        submission = self.repository.get_by_id(submission_id)
        if submission is None:
            raise ValueError(f"Submission with ID {submission_id} not found.")
        return submission

    def list_submissions(
        self, skip: int = 0, limit: int = 100, channel: Optional[str] = None
    ) -> list[Submission]:
        return self.repository.get_filtered(skip=skip, limit=limit, channel=channel)

from typing import Optional
from sqlalchemy.orm import Session
from Repository.citizen_contact_repository import CitizenContactRepository
from Entity.citizen_contact_entity import CitizenContact
from Utils.hashing import tokenise_identifier


class CitizenContactService:
    """
    Resolves a citizen's raw contact identifier (e.g. phone number) supplied
    at intake into a PII-separated CitizenContact record, storing only a
    deterministic token — never the raw value (DR-003, DR-007).

    Anonymous reporting is supported: pass raw_identifier=None to skip
    contact resolution entirely.
    """

    def __init__(self, db: Session):
        self.repository = CitizenContactRepository(db)

    def find_or_create(
        self,
        raw_identifier: Optional[str],
        preferred_channel: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> Optional[CitizenContact]:
        if not raw_identifier:
            return None

        token = tokenise_identifier(raw_identifier)
        existing = self.repository.get_by_token(token)
        if existing is not None:
            return existing

        contact = CitizenContact(
            encrypted_phone=token,
            preferred_channel=preferred_channel,
            language_code=language_code,
        )
        return self.repository.create(contact)

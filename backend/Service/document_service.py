import hashlib
import os
import re
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from Repository.document_repository import DocumentRepository
from Repository.submission_repository import SubmissionRepository
from Entity.document_entity import Document
from Utils.Enums import MalwareStatusEnum

_UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


class DocumentService:
    """
    Business logic for uploaded report attachments (FR-005).

    Binary content is stored on local disk for this prototype pass — never
    inline in the database — matching the architecture doc's "no binary
    data in event" rule for the canonical intake schema.

    OCR extraction is a deliberate no-op here: ocr_text/extraction_json are
    left null pending a provider integration (no OCR credentials exist in
    this environment). Real malware scanning is likewise deferred to the
    pilot — malware_status is set to CLEAN outright so the prototype demo
    path isn't blocked. Both are documented gaps, not oversights.
    """

    def __init__(self, db: Session):
        self.repository = DocumentRepository(db)
        self.submission_repository = SubmissionRepository(db)

    def upload_document(
        self,
        submission_id,
        file_bytes: bytes,
        mime_type: str,
        original_filename: Optional[str],
    ) -> Document:
        submission = self.submission_repository.get_by_id(submission_id)
        if submission is None:
            raise ValueError(f"Submission with ID {submission_id} not found.")

        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        safe_name = _SAFE_FILENAME_RE.sub("_", original_filename or "upload")
        storage_dir = os.path.join(_UPLOAD_ROOT, str(submission_id))
        os.makedirs(storage_dir, exist_ok=True)
        storage_path = os.path.join(storage_dir, f"{uuid.uuid4()}_{safe_name}")
        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        document = Document(
            submission_id=submission_id,
            file_hash=hashlib.sha256(file_bytes).hexdigest(),
            mime_type=mime_type,
            original_filename=original_filename,
            storage_ref=storage_path,
            malware_status=MalwareStatusEnum.CLEAN.value,
        )
        document = self.repository.create(document)

        refs = list(submission.attachment_refs or [])
        refs.append(str(document.id))
        self.submission_repository.update(submission, {"attachment_refs": refs})

        return document

    def get_document(self, document_id) -> Document:
        document = self.repository.get_by_id(document_id)
        if document is None:
            raise ValueError(f"Document with ID {document_id} not found.")
        return document

    def list_for_submission(self, submission_id) -> list[Document]:
        return self.repository.list_by_submission(submission_id)

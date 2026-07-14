from datetime import datetime, timezone
import os
import urllib.request
import json
from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from Repository.case_repository import CaseRepository
from Repository.submission_repository import SubmissionRepository
from Repository.queue_repository import QueueRepository
from Service.audit_event_service import AuditEventService
from Service.classification_service import classify, CLASSIFICATION_CONFIDENCE_THRESHOLD
from Service.routing_service import recommend_queue
from Config.variables import GEMINI_FLASH_MODEL
from Entity.case_entity import Case
from Utils.Enums import CaseStatusEnum, ConsentStatusEnum, UrgencyEnum
from Utils.service_categories import URGENCY_SLA

# ---------------------------------------------------------------------------
# Case lifecycle state machine (architecture doc §5). MANUAL_REVIEW,
# NEEDS_INFORMATION, ON_HOLD, ESCALATED and REOPENED only appear as inbound
# *targets* in that table — the doc does not define their own outbound
# transitions, so the entries below marked "extension" are this
# implementation's own reasonable continuation, not a spec requirement.
# ---------------------------------------------------------------------------
ALLOWED_TRANSITIONS: dict[str, set] = {
    CaseStatusEnum.RECEIVED.value: {CaseStatusEnum.VALIDATING.value, CaseStatusEnum.REJECTED.value},
    CaseStatusEnum.VALIDATING.value: {
        CaseStatusEnum.CLASSIFIED.value,
        CaseStatusEnum.NEEDS_INFORMATION.value,
        CaseStatusEnum.REJECTED.value,
    },
    CaseStatusEnum.CLASSIFIED.value: {CaseStatusEnum.ROUTED.value, CaseStatusEnum.MANUAL_REVIEW.value},
    CaseStatusEnum.ROUTED.value: {CaseStatusEnum.ASSIGNED.value, CaseStatusEnum.ESCALATED.value},
    CaseStatusEnum.ASSIGNED.value: {CaseStatusEnum.IN_PROGRESS.value, CaseStatusEnum.ESCALATED.value},
    CaseStatusEnum.IN_PROGRESS.value: {
        CaseStatusEnum.RESOLVED.value,
        CaseStatusEnum.ON_HOLD.value,
        CaseStatusEnum.ESCALATED.value,
    },
    CaseStatusEnum.RESOLVED.value: {CaseStatusEnum.CLOSED.value, CaseStatusEnum.REOPENED.value},
    CaseStatusEnum.CLOSED.value: {CaseStatusEnum.REOPENED.value},
    CaseStatusEnum.REJECTED.value: {CaseStatusEnum.MANUAL_REVIEW.value},
    # --- extensions, not in the architecture doc's table ---
    CaseStatusEnum.MANUAL_REVIEW.value: {
        CaseStatusEnum.CLASSIFIED.value,
        CaseStatusEnum.ROUTED.value,
        CaseStatusEnum.REJECTED.value,
    },
    CaseStatusEnum.NEEDS_INFORMATION.value: {
        CaseStatusEnum.VALIDATING.value,
        CaseStatusEnum.REJECTED.value,
    },
    CaseStatusEnum.ON_HOLD.value: {
        CaseStatusEnum.IN_PROGRESS.value,
        CaseStatusEnum.ESCALATED.value,
        CaseStatusEnum.CLOSED.value,
    },
    CaseStatusEnum.ESCALATED.value: {
        CaseStatusEnum.ASSIGNED.value,
        CaseStatusEnum.IN_PROGRESS.value,
        CaseStatusEnum.RESOLVED.value,
    },
    CaseStatusEnum.REOPENED.value: {
        CaseStatusEnum.VALIDATING.value,
        CaseStatusEnum.ASSIGNED.value,
        CaseStatusEnum.IN_PROGRESS.value,
    },
}

_MAX_REFERENCE_NUMBER_ATTEMPTS = 3


class CaseService:
    """
    Business logic for the operational Case pipeline: intake validation,
    rule-based classification, jurisdiction routing and lifecycle
    transitions. No FastAPI imports — raises ValueError for all rule
    violations. Every state-changing action is audited (FR-022).
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = CaseRepository(db)
        self.submission_repository = SubmissionRepository(db)
        self.audit_service = AuditEventService(db)

    # -- reference numbers --------------------------------------------------

    def _next_reference_number(self) -> str:
        year = datetime.now(timezone.utc).year
        prefix = f"SF-{year}-"
        count = self.repository.count_by_reference_prefix(prefix)
        return f"{prefix}{count + 1:05d}"

    # -- translation helper -------------------------------------------------

    def _translate_to_english_if_needed(self, text: str) -> Optional[str]:
        """
        Uses Gemini to check if the text needs translation to English.
        If it's not English, translates it.
        If it's already English, returns 'ALREADY_ENGLISH'.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY is not configured in .env. Skipping translation.")
            return "ALREADY_ENGLISH"

        prompt = (
            "You are an expert translator. Check if the following text is in English.\n"
            "If the text is in English, reply with exactly \"ALREADY_ENGLISH\".\n"
            "If the text is not in English (e.g. it is in Shona, Ndebele, Zulu, Sesotho, etc.), "
            "translate it to English and reply ONLY with the translated English text. "
            "Do not add any formatting, notes, intro, or explanations.\n\n"
            f"Text: \"{text}\""
        )

        api_key_clean = api_key.strip('"\'')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_FLASH_MODEL}:generateContent?key={api_key_clean}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0}
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                result = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if result.startswith('"') and result.endswith('"'):
                    result = result[1:-1].strip()
                return result
        except Exception as e:
            print(f"Error invoking Gemini translation: {e}")
            return "ALREADY_ENGLISH"

    # -- pipeline -------------------------------------------------------

    def create_case_from_submission(
        self,
        submission_id,
        actor_user_id: Optional[int] = None,
        actor_channel: Optional[str] = None,
    ) -> Case:
        submission = self.submission_repository.get_by_id(submission_id)
        if submission is None:
            raise ValueError(f"Submission with ID {submission_id} not found.")

        # "case.created" is genuinely attributable to whoever submitted the
        # report (or the officer/dispatcher who filed it on the citizen's
        # behalf) — actor_user_id/actor_channel here are the real submitter.
        case = self._create_received_case(submission, actor_user_id, actor_channel)

        # Everything from here on is the automated intake pipeline — no
        # human chose these outcomes, so they're attributed to a system
        # actor (actor_user_id=None) with a descriptive actor_channel
        # instead of the submitter, so the case roadmap can tell citizens
        # and staff which steps were AI/automation versus a human decision.
        if submission.consent_status == ConsentStatusEnum.DECLINED.value:
            return self._transition(
                case, CaseStatusEnum.REJECTED.value, actor_user_id=None,
                actor_channel="automated_validation",
                reason="Citizen declined consent at intake.",
            )

        case = self._transition(
            case, CaseStatusEnum.VALIDATING.value, actor_user_id=None,
            actor_channel="automated_validation",
            reason="Automated validation passed.",
        )

        # ── TRANSLATION CHECK ──
        # Check if the description needs translation to English.
        english_description = None
        translation_result = self._translate_to_english_if_needed(submission.service_description)
        if translation_result and translation_result != "ALREADY_ENGLISH":
            english_description = translation_result
            case = self.repository.update(case, {"english_description": english_description})
            classify_text = english_description
        else:
            classify_text = submission.service_description

        # Classification runs on the English text (either translated or original)
        result = classify(classify_text)
        case = self._apply_classification(
            case, result, actor_user_id=None, actor_channel="ai_classifier",
        )

        # Classification always produces a suggestion (architecture §5:
        # CLASSIFIED's entry condition is "category/urgency suggested",
        # independent of confidence) — confidence only gates what happens
        # *after* CLASSIFIED: auto-route, or fall back to MANUAL_REVIEW.
        case = self._transition(
            case, CaseStatusEnum.CLASSIFIED.value, actor_user_id=None,
            actor_channel="ai_classifier",
            reason="Category/urgency suggested by the classification baseline.",
        )

        if result.confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD:
            case = self._transition(
                case, CaseStatusEnum.MANUAL_REVIEW.value, actor_user_id=None,
                actor_channel="ai_classifier",
                reason=(
                    f"Classification confidence {result.confidence} below "
                    f"threshold {CLASSIFICATION_CONFIDENCE_THRESHOLD}."
                ),
            )
        else:
            queue = recommend_queue(self.db, result.category, case.district_id)
            if queue is not None:
                case = self.repository.update(case, {"queue_id": queue.id})
                case = self._transition(
                    case, CaseStatusEnum.ROUTED.value, actor_user_id=None,
                    actor_channel="auto_router",
                    reason=f"Auto-routed to queue {queue.id}.",
                )

        # Send SMS notification of case creation to citizen
        if case.status != CaseStatusEnum.REJECTED.value and case.contact_phone:
            try:
                from Service.sms_service import SMSService
                sms_service = SMSService()
                clean_phone = case.contact_phone.replace("whatsapp:", "").strip()
                if clean_phone:
                    lang = submission.language_code or "en"
                    if lang == "sn":
                        msg = f"Ndatenda! Chichemo chenyu chatambirwa. Reference Number: {case.reference_number}. Tichakuzivisai kana chagadziriswa."
                    elif lang in ["zu", "nd"]:
                        msg = f"Ngiyabonga! Umbiko wenu wamukelwe. Reference Number: {case.reference_number}. Sizokwazisa uma usulungisiwe."
                    else:
                        msg = f"Thank you! Your report has been received. Reference Number: {case.reference_number}. We will notify you once it is resolved."
                    sms_service.send_sms(msg, [clean_phone])
            except Exception as e:
                print(f"Failed to send case creation SMS: {e}")

        return case

    def _create_received_case(self, submission, actor_user_id, actor_channel) -> Case:
        last_error = None
        for _ in range(_MAX_REFERENCE_NUMBER_ATTEMPTS):
            case = Case(
                reference_number=self._next_reference_number(),
                category="unclassified",
                urgency=UrgencyEnum.MEDIUM.value,
                status=CaseStatusEnum.RECEIVED.value,
                description=submission.service_description,
                english_description=None,
                contact_email=submission.contact_email,
                contact_phone=submission.contact_phone,
                submission_id=submission.id,
                district_id=submission.district_id,
                opened_at=datetime.now(timezone.utc),
            )
            try:
                case = self.repository.create(case)
            except IntegrityError as exc:
                self.db.rollback()
                last_error = exc
                continue

            self.audit_service.log(
                action="case.created",
                object_type="case",
                object_id=str(case.id),
                actor_user_id=actor_user_id,
                actor_channel=actor_channel,
                after={
                    "reference_number": case.reference_number,
                    "submission_id": str(submission.id),
                },
                detail={"reference_number": case.reference_number},
            )
            return case

        raise ValueError(
            "Failed to allocate a unique case reference number after multiple attempts."
        ) from last_error

    def _apply_classification(
        self, case: Case, result, actor_user_id, actor_channel: Optional[str] = None,
    ) -> Case:
        before = {
            "category": case.category,
            "subcategory": case.subcategory,
            "urgency": case.urgency,
            "classification_confidence": case.classification_confidence,
        }
        sla_deadline = datetime.now(timezone.utc) + URGENCY_SLA.get(
            result.urgency, URGENCY_SLA[UrgencyEnum.MEDIUM.value]
        )
        case = self.repository.update(case, {
            "category": result.category,
            "subcategory": result.subcategory,
            "urgency": result.urgency,
            "classification_confidence": result.confidence,
            "sla_deadline": sla_deadline,
        })
        after = {
            "category": case.category,
            "subcategory": case.subcategory,
            "urgency": case.urgency,
            "classification_confidence": case.classification_confidence,
        }
        self.audit_service.log(
            action="case.classified",
            object_type="case",
            object_id=str(case.id),
            actor_user_id=actor_user_id,
            actor_channel=actor_channel,
            before=before,
            after=after,
            detail=after,
        )
        return case

    # -- officer / dispatcher actions ---------------------------------------

    def correct_classification(
        self, case_id, category: str, subcategory: Optional[str], urgency: str,
        actor_user_id: Optional[int] = None,
    ) -> Case:
        case = self.get_case(case_id)
        if case.status not in {CaseStatusEnum.CLASSIFIED.value, CaseStatusEnum.MANUAL_REVIEW.value}:
            raise ValueError(
                f"Cannot correct classification while case is in status '{case.status}'."
            )

        before = {
            "category": case.category,
            "subcategory": case.subcategory,
            "urgency": case.urgency,
            "classification_confidence": case.classification_confidence,
        }
        case = self.repository.update(case, {
            "category": category,
            "subcategory": subcategory,
            "urgency": urgency,
            "classification_confidence": 1.0,  # officer-confirmed
        })
        after = {"category": category, "subcategory": subcategory, "urgency": urgency}
        self.audit_service.log(
            action="case.classification_corrected",
            object_type="case",
            object_id=str(case.id),
            actor_user_id=actor_user_id,
            before=before,
            after=after,
            detail=after,
        )

        if case.status == CaseStatusEnum.MANUAL_REVIEW.value:
            case = self._transition(
                case, CaseStatusEnum.CLASSIFIED.value, actor_user_id,
                reason="Officer corrected classification.",
            )

        # The re-route that follows a correction is still an algorithmic
        # queue match, not a human queue choice — attributed to the system,
        # same as the initial auto-route, even though the correction itself
        # (logged above) was the officer's decision.
        queue = recommend_queue(self.db, category, case.district_id)
        if queue is not None:
            case = self.repository.update(case, {"queue_id": queue.id})
            case = self._transition(
                case, CaseStatusEnum.ROUTED.value, actor_user_id=None,
                actor_channel="auto_router",
                reason=f"Auto-routed to queue {queue.id} after correction.",
            )
        return case

    def route_case(self, case_id, queue_id: Optional[int], actor_user_id: Optional[int] = None) -> Case:
        case = self.get_case(case_id)
        if case.status not in {CaseStatusEnum.CLASSIFIED.value, CaseStatusEnum.MANUAL_REVIEW.value}:
            raise ValueError(f"Cannot route case while case is in status '{case.status}'.")

        if queue_id is not None:
            queue = QueueRepository(self.db).get_by_id(queue_id)
            if queue is None or not queue.is_active:
                raise ValueError(f"Queue {queue_id} not found or inactive.")
        else:
            queue = recommend_queue(self.db, case.category, case.district_id)
            if queue is None:
                raise ValueError(
                    "No matching queue found for this case's category/district; "
                    "specify queue_id explicitly."
                )

        case = self.repository.update(case, {"queue_id": queue.id})
        if case.status == CaseStatusEnum.MANUAL_REVIEW.value:
            case = self._transition(
                case, CaseStatusEnum.CLASSIFIED.value, actor_user_id,
                reason="Dispatcher routed a manual-review case.",
            )
        return self._transition(
            case, CaseStatusEnum.ROUTED.value, actor_user_id,
            reason=f"Dispatcher confirmed routing to queue {queue.id}.",
        )

    def update_status(
        self, case_id, new_status: str, reason: str, actor_user_id: Optional[int] = None,
    ) -> Case:
        case = self.get_case(case_id)
        return self._transition(case, new_status, actor_user_id, reason=reason)

    # -- reads -------------------------------------------------------------

    def get_case(self, case_id) -> Case:
        case = self.repository.get_by_id(case_id)
        if case is None:
            raise ValueError(f"Case with ID {case_id} not found.")
        return case

    @staticmethod
    def is_owned_by_citizen(case: Case, user_id: int) -> bool:
        """True if the case's originating submission was made by this user.

        Shared by the case-detail endpoint and the audit-events carve-out
        below so "does this citizen own this case" is defined exactly once.
        """
        return case.submission is not None and case.submission.submitter_user_id == user_id

    def list_cases(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None,
        district_id: Optional[int] = None, queue_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> list[Case]:
        return self.repository.get_filtered(
            skip=skip, limit=limit, status=status,
            district_id=district_id, queue_id=queue_id, category=category,
        )

    def list_my_cases(
        self, submitter_user_id: int, skip: int = 0, limit: int = 100,
        status: Optional[str] = None, category: Optional[str] = None,
    ) -> list[Case]:
        """Return only the cases that belong to the authenticated citizen."""
        return self.repository.get_filtered_for_citizen(
            submitter_user_id=submitter_user_id,
            skip=skip, limit=limit, status=status, category=category,
        )

    def get_case_summary(
        self, group_by: str = "status", status: Optional[str] = None,
        district_id: Optional[int] = None, queue_id: Optional[int] = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        valid_group_by = {"status", "category", "district_id", "queue_id"}
        if group_by not in valid_group_by:
            raise ValueError(f"group_by must be one of {sorted(valid_group_by)}.")
        rows = self.repository.count_by_group(
            group_by, status=status, district_id=district_id,
            queue_id=queue_id, category=category,
        )
        return [{"key": key, "count": count} for key, count in rows]

    # -- internals -----------------------------------------------------

    def _transition(
        self, case: Case, new_status: str, actor_user_id: Optional[int], reason: str,
        actor_channel: Optional[str] = None,
    ) -> Case:
        allowed = ALLOWED_TRANSITIONS.get(case.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition case from '{case.status}' to '{new_status}'. "
                f"Allowed next states: {sorted(allowed) or 'none'}."
            )

        before = {"status": case.status}
        from_status = case.status
        update_data = {"status": new_status}
        if new_status == CaseStatusEnum.CLOSED.value:
            update_data["closed_at"] = datetime.now(timezone.utc)

        case = self.repository.update(case, update_data)

        self.audit_service.log(
            action="case.status_changed",
            object_type="case",
            object_id=str(case.id),
            actor_user_id=actor_user_id,
            actor_channel=actor_channel,
            before=before,
            after={"status": case.status, "reason": reason},
            detail={"from": from_status, "to": case.status, "reason": reason},
        )

        # Trigger resolution SMS if transitioned to RESOLVED
        if new_status == CaseStatusEnum.RESOLVED.value and case.contact_phone:
            try:
                from Service.sms_service import SMSService
                sms_service = SMSService()
                clean_phone = case.contact_phone.replace("whatsapp:", "").strip()
                if clean_phone:
                    lang = "en"
                    if case.submission:
                        lang = case.submission.language_code or "en"
                    
                    if lang == "sn":
                        msg = f"Mufaro mukuru! Chichemo chenyu (Reference Number: {case.reference_number}) chagadziriswa. Maita basa nekushandisa mushando wedu."
                    elif lang in ["zu", "nd"]:
                        msg = f"Izindaba ezinhle! Umbiko wenu (Reference Number: {case.reference_number}) usulungisiwe. Ngiyabonga ngokusebenzisa isizinda sethu."
                    else:
                        msg = f"Good news! Your report (Reference Number: {case.reference_number}) has been resolved. Thank you for using our service."
                    sms_service.send_sms(msg, [clean_phone])
            except Exception as e:
                print(f"Failed to send case resolution SMS: {e}")

        return case

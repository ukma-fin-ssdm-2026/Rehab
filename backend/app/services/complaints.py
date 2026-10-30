# AI-GENERATED START
"""Скарги підопічного на ментора, їх розгляд і агрегати адмінки.

Функції не викликають commit/rollback: транзакцією керує маршрут.
Порядок блокувань як у mentorship.py: users підопічного → mentorships → complaints.
"""

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.clock import BUSINESS_TIMEZONE, utc_now
from backend.app.db.models.complaint import Complaint
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.support_comment import SupportComment
from backend.app.db.models.user import User
from backend.app.errors import api_error
from backend.app.schemas.complaints import (
    AdminComplaintOut,
    AdminOverview,
    ComplaintCreate,
    ComplaintEvidence,
    ComplaintParty,
)
from backend.app.services.mentorship import end_relationship_for_complaint

REGISTRATION_DAYS = 30


def _not_found() -> Exception:
    return api_error(404, "MENTORSHIP_NOT_FOUND", "Менторство не знайдено")


def _lock_relationship(db: Session, relationship_id: int) -> Mentorship:
    mentee_id = db.scalar(
        select(Mentorship.mentee_id).where(
            Mentorship.relationship_id == relationship_id
        )
    )
    if mentee_id is None:
        raise _not_found()
    db.scalar(select(User.user_id).where(User.user_id == mentee_id).with_for_update())
    return db.scalar(
        select(Mentorship)
        .where(Mentorship.relationship_id == relationship_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def submit_complaint(db: Session, actor_id: int, payload: ComplaintCreate) -> Complaint:
    relationship = _lock_relationship(db, payload.relationship_id)
    if actor_id == relationship.mentor_id:
        raise api_error(
            403, "FORBIDDEN", "Скаргу на ментора подає лише його підопічний"
        )
    if actor_id != relationship.mentee_id:
        raise _not_found()

    evidence = None
    if payload.support_comment_id is not None:
        evidence = db.get(SupportComment, payload.support_comment_id)
        if (
            evidence is None
            or evidence.relationship_id != relationship.relationship_id
            or evidence.author_id != relationship.mentor_id
            or evidence.recipient_id != actor_id
        ):
            raise api_error(
                404, "SUPPORT_COMMENT_NOT_FOUND", "Коментар підтримки не знайдено"
            )

    pending = db.scalar(
        select(Complaint.complaint_id).where(
            Complaint.reporter_id == actor_id,
            Complaint.reported_id == relationship.mentor_id,
            Complaint.status == "pending",
        )
    )
    if pending is not None:
        raise _already_pending()

    complaint = Complaint(
        relationship_id=relationship.relationship_id,
        reporter_id=actor_id,
        reported_id=relationship.mentor_id,
        reason=payload.reason,
        support_comment_id=evidence.support_comment_id if evidence else None,
        evidence_text=evidence.text if evidence else None,
        evidence_created_at=evidence.created_at if evidence else None,
    )
    db.add(complaint)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise _already_pending() from None
    return complaint


def _already_pending() -> Exception:
    return api_error(
        409, "COMPLAINT_ALREADY_PENDING", "Скарга на цього ментора вже розглядається"
    )


def get_complaint(db: Session, complaint_id: int) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise api_error(404, "COMPLAINT_NOT_FOUND", "Скаргу не знайдено")
    return complaint


def decide_complaint(
    db: Session, complaint_id: int, admin_id: int, decision: str
) -> Complaint:
    complaint = get_complaint(db, complaint_id)
    _lock_relationship(db, complaint.relationship_id)
    complaint = db.scalar(
        select(Complaint)
        .where(Complaint.complaint_id == complaint_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if complaint.status == decision:
        return complaint
    if complaint.status != "pending":
        raise api_error(
            409, "COMPLAINT_ALREADY_REVIEWED", "Скаргу вже розглянуто з іншим рішенням"
        )
    if decision == "approved":
        end_relationship_for_complaint(db, complaint.relationship_id, admin_id)
    complaint.status = decision
    complaint.reviewed_at = utc_now()
    complaint.reviewed_by = admin_id
    db.flush()
    return complaint


def list_complaints(
    db: Session, status: str, limit: int, offset: int
) -> tuple[list[Complaint], int]:
    query = select(Complaint)
    if status != "all":
        query = query.where(Complaint.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Complaint.created_at.desc(), Complaint.complaint_id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(rows), total


def to_admin_out(db: Session, complaint: Complaint) -> AdminComplaintOut:
    reporter = db.get(User, complaint.reporter_id)
    reported = db.get(User, complaint.reported_id)
    evidence = (
        ComplaintEvidence(
            text=complaint.evidence_text, created_at=complaint.evidence_created_at
        )
        if complaint.evidence_text is not None
        else None
    )
    return AdminComplaintOut(
        complaint_id=complaint.complaint_id,
        relationship_id=complaint.relationship_id,
        reason=complaint.reason,
        support_comment_id=complaint.support_comment_id,
        status=complaint.status,
        created_at=complaint.created_at,
        reviewed_at=complaint.reviewed_at,
        reporter=ComplaintParty.model_validate(reporter),
        reported=ComplaintParty.model_validate(reported),
        evidence=evidence,
    )


def registration_window(today: dt.date) -> tuple[dt.datetime, dt.datetime]:
    """Від початку київського дня today-29 до початку київського завтра."""
    start = dt.datetime.combine(
        today - dt.timedelta(days=REGISTRATION_DAYS - 1),
        dt.time.min,
        BUSINESS_TIMEZONE,
    )
    end = dt.datetime.combine(
        today + dt.timedelta(days=1), dt.time.min, BUSINESS_TIMEZONE
    )
    return start, end


def admin_overview(db: Session, today: dt.date) -> AdminOverview:
    start, end = registration_window(today)
    registrations = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role != "admin", User.created_at >= start, User.created_at < end)
    )
    active = select(Mentorship).where(Mentorship.status == "active").subquery()
    return AdminOverview(
        registrations_last_30_days=registrations or 0,
        active_mentors=db.scalar(select(func.count(func.distinct(active.c.mentor_id))))
        or 0,
        active_relationships=db.scalar(select(func.count()).select_from(active)) or 0,
        pending_complaints=db.scalar(
            select(func.count())
            .select_from(Complaint)
            .where(Complaint.status == "pending")
        )
        or 0,
        current_date=today,
    )


# AI-GENERATED END

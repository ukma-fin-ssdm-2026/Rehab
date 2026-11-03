"""Shared SQL authorization boundary. The caller owns commit/rollback.

Lock order for all writers: mentee user, relationship, then entry/notification.
The router is independently mountable; shared app registration is an integration step.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.clock import utc_now
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.user import User
from backend.app.errors import api_error


def _relationship(
    db: Session, relationship_id: int, *, lock: bool = False
) -> Mentorship:
    query = select(Mentorship).where(Mentorship.relationship_id == relationship_id)
    if lock:
        mentee_id = db.scalar(
            select(Mentorship.mentee_id).where(
                Mentorship.relationship_id == relationship_id
            )
        )
        if mentee_id is None:
            raise api_error(404, "MENTORSHIP_NOT_FOUND", "Менторство не знайдено")
        db.scalar(
            select(User.user_id)
            .where(User.user_id == mentee_id)
            .with_for_update(key_share=True)
        )
        query = query.with_for_update()
    # A Session may have seen the relationship before another writer revoked it.
    result = db.scalar(query.execution_options(populate_existing=True))
    if result is None:
        raise api_error(404, "MENTORSHIP_NOT_FOUND", "Менторство не знайдено")
    return result


def join_by_code(db: Session, actor_id: int, code: str) -> tuple[Mentorship, bool]:
    """Serialize joining on the mentee without blocking FK references to the mentor."""
    actor_role = db.scalar(select(User.role).where(User.user_id == actor_id))
    if actor_role not in ("user", "mentor"):
        raise api_error(403, "FORBIDDEN", "Недостатньо прав")
    target = db.scalar(
        select(User)
        .where(
            User.mentor_code == code,
            User.role.in_(("user", "mentor")),
        )
        .with_for_update(key_share=True)
        .execution_options(populate_existing=True)
    )
    if target is None:
        raise api_error(404, "INVALID_MENTOR_CODE", "Код не знайдено")
    if target.user_id == actor_id:
        raise api_error(
            422, "SELF_MENTORSHIP_NOT_ALLOWED", "Не можна стати ментором самого себе"
        )
    existing = db.scalar(
        select(Mentorship)
        .where(
            Mentorship.mentor_id == actor_id,
            Mentorship.mentee_id == target.user_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if existing is not None:
        if existing.status == "ended":
            raise api_error(
                403,
                "MENTORSHIP_REJOIN_FORBIDDEN",
                "Повторне приєднання цієї пари заборонено",
            )
        return existing, False
    active = db.scalar(
        select(Mentorship.relationship_id).where(
            Mentorship.mentee_id == target.user_id,
            Mentorship.status == "active",
        )
    )
    if active is not None:
        raise api_error(
            409, "MENTEE_ALREADY_HAS_MENTOR", "Цей користувач уже має ментора"
        )
    result = Mentorship(mentor_id=actor_id, mentee_id=target.user_id)
    db.add(result)
    db.flush()
    return result, True


def require_relationship_participant(
    db: Session, actor_id: int, relationship_id: int
) -> Mentorship:
    result = _relationship(db, relationship_id)
    if actor_id not in (result.mentor_id, result.mentee_id):
        raise api_error(404, "MENTORSHIP_NOT_FOUND", "Менторство не знайдено")
    return result


def require_active_mentor(
    db: Session, actor_id: int, relationship_id: int, *, lock: bool = False
) -> Mentorship:
    result = _relationship(db, relationship_id, lock=lock)
    if result.mentor_id != actor_id:
        raise api_error(404, "MENTORSHIP_NOT_FOUND", "Менторство не знайдено")
    if result.status != "active":
        raise api_error(403, "MENTORSHIP_INACTIVE", "Менторство завершено")
    return result


def _end(db: Session, result: Mentorship, actor_id: int, reason: str) -> Mentorship:
    if result.status == "active":
        result.status = "ended"
        result.ended_at = utc_now()
        result.ended_by = actor_id
        result.ended_reason = reason
        db.flush()
    return result


def end_relationship(
    db: Session, relationship_id: int, actor_id: int, reason: str
) -> Mentorship:
    result = _relationship(db, relationship_id, lock=True)
    if actor_id not in (result.mentor_id, result.mentee_id):
        raise api_error(404, "MENTORSHIP_NOT_FOUND", "Менторство не знайдено")
    expected = "mentor_left" if actor_id == result.mentor_id else "mentee_left"
    if reason != expected:
        raise api_error(
            403, "FORBIDDEN", "Недостатньо прав для цієї причини завершення"
        )
    return _end(db, result, actor_id, reason)


def end_relationship_for_complaint(
    db: Session, relationship_id: int, admin_id: int
) -> Mentorship:
    if db.scalar(select(User.role).where(User.user_id == admin_id)) != "admin":
        raise api_error(403, "FORBIDDEN", "Потрібна роль admin")
    result = _relationship(db, relationship_id, lock=True)
    return _end(db, result, admin_id, "complaint")

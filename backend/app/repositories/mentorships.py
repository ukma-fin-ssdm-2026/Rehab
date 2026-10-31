"""SQL reads and public projections, without credentials or commit calls."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.user import User
from backend.app.schemas.mentorship import RelationshipContact, RelationshipOut


def current_mentor(db: Session, mentee_id: int) -> Mentorship | None:
    return db.scalar(
        select(Mentorship)
        .where(
            Mentorship.mentee_id == mentee_id,
            Mentorship.status == "active",
        )
        .execution_options(populate_existing=True)
    )


def mentees_page(db: Session, mentor_id: int, limit: int, offset: int):
    filters = (Mentorship.mentor_id == mentor_id, Mentorship.status == "active")
    total = db.scalar(select(func.count()).select_from(Mentorship).where(*filters)) or 0
    rows = list(
        db.scalars(
            select(Mentorship)
            .where(*filters)
            .order_by(
                Mentorship.created_at.desc(),
                Mentorship.relationship_id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return rows, total


def public_relationships(db: Session, rows: list[Mentorship]) -> list[RelationshipOut]:
    if not rows:
        return []
    ids = {uid for row in rows for uid in (row.mentor_id, row.mentee_id)}
    # One bounded contact query per page, rather than one query per mentee.
    contacts = {
        row.user_id: RelationshipContact.model_validate(row._mapping)
        for row in db.execute(
            select(User.user_id, User.nickname, User.email).where(User.user_id.in_(ids))
        )
    }
    return [
        RelationshipOut(
            relationship_id=row.relationship_id,
            status=row.status,
            mentor=contacts[row.mentor_id],
            mentee=contacts[row.mentee_id],
            created_at=row.created_at,
            ended_at=row.ended_at,
            ended_reason=row.ended_reason,
        )
        for row in rows
    ]

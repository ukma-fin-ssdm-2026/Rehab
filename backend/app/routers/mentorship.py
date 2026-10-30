"""Mentorship and read-only mentee API. No write access to another calendar."""

import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from backend.app.core.clock import today_local
from backend.app.db.session import get_db
from backend.app.errors import COMMON_RESPONSES, api_error
from backend.app.models import EntryList, EntryOut, StatisticsOut
from backend.app.repositories import entries, mentorships
from backend.app.repositories.users import get_user
from backend.app.schemas.mentorship import (
    MentorshipCreate,
    MentorCodeOut,
    RelationshipOut,
    RelationshipItem,
    RelationshipList,
)
from backend.app.security import CurrentUser, require_role
from backend.app.services.mentorship import (
    end_relationship,
    join_by_code,
    require_active_mentor,
    require_relationship_participant,
)
from backend.app.services.statistics import calculate_statistics

router = APIRouter(
    prefix="/mentorships", tags=["Mentorship"], responses=COMMON_RESPONSES
)
ordinary_user = require_role("user", "mentor")


@router.get("/code", response_model=MentorCodeOut)
def own_code(user: CurrentUser = Depends(ordinary_user), db: Session = Depends(get_db)):
    return MentorCodeOut(code=get_user(db, user.user_id).mentor_code)


@router.get("/my-mentor", response_model=RelationshipItem)
def my_mentor(
    user: CurrentUser = Depends(ordinary_user), db: Session = Depends(get_db)
):
    row = mentorships.current_mentor(db, user.user_id)
    return RelationshipItem(
        item=mentorships.public_relationships(db, [row])[0] if row else None
    )


@router.get("/my-mentees", response_model=RelationshipList)
def my_mentees(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(ordinary_user),
    db: Session = Depends(get_db),
):
    rows, total = mentorships.mentees_page(db, user.user_id, limit, offset)
    return RelationshipList(
        items=mentorships.public_relationships(db, rows),
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    status_code=201,
    response_model=RelationshipOut,
    responses={200: {"model": RelationshipOut}},
)
def join(
    body: MentorshipCreate,
    response: Response,
    user: CurrentUser = Depends(ordinary_user),
    db: Session = Depends(get_db),
):
    row, created = join_by_code(db, user.user_id, body.code)
    result = mentorships.public_relationships(db, [row])[0]
    db.commit()
    response.status_code = 201 if created else 200
    return result


@router.get("/{relationship_id}", response_model=RelationshipOut)
def relationship(
    relationship_id: int = Path(ge=1),
    user: CurrentUser = Depends(ordinary_user),
    db: Session = Depends(get_db),
):
    row = require_relationship_participant(db, user.user_id, relationship_id)
    return mentorships.public_relationships(db, [row])[0]


@router.delete("/{relationship_id}", status_code=204)
def leave(
    relationship_id: int = Path(ge=1),
    user: CurrentUser = Depends(ordinary_user),
    db: Session = Depends(get_db),
):
    row = require_relationship_participant(db, user.user_id, relationship_id)
    reason = "mentor_left" if row.mentor_id == user.user_id else "mentee_left"
    end_relationship(db, relationship_id, user.user_id, reason)
    db.commit()
    return Response(status_code=204)


@router.get("/{relationship_id}/calendar/entries", response_model=EntryList)
def mentee_entries(
    relationship_id: int = Path(ge=1),
    date_from: dt.date | None = Query(None, alias="from"),
    date_to: dt.date | None = Query(None, alias="to"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(ordinary_user),
    db: Session = Depends(get_db),
):
    row = require_active_mentor(db, user.user_id, relationship_id, lock=True)
    if date_from and date_to and date_from > date_to:
        raise api_error(422, "INVALID_DATE_RANGE", "Початок періоду пізніше завершення")
    return EntryList(
        items=entries.list_user_entries(
            db, row.mentee_id, date_from, date_to, limit=limit, offset=offset
        ),
        total=entries.count_user_entries(db, row.mentee_id, date_from, date_to),
        limit=limit,
        offset=offset,
    )


@router.get("/{relationship_id}/calendar/entries/{record_id}", response_model=EntryOut)
def mentee_entry(
    relationship_id: int = Path(ge=1),
    record_id: int = Path(ge=1),
    user: CurrentUser = Depends(ordinary_user),
    db: Session = Depends(get_db),
):
    row = require_active_mentor(db, user.user_id, relationship_id, lock=True)
    try:
        return entries.get_own_entry(db, row.mentee_id, record_id)
    except entries.EntryNotFound as error:
        raise api_error(404, "ENTRY_NOT_FOUND", "Запис не знайдено") from error


@router.get("/{relationship_id}/statistics", response_model=StatisticsOut)
def mentee_statistics(
    relationship_id: int = Path(ge=1),
    period: Literal["all", "week", "month", "year"] = Query("all"),
    user: CurrentUser = Depends(ordinary_user),
    db: Session = Depends(get_db),
):
    row = require_active_mentor(db, user.user_id, relationship_id, lock=True)
    account = get_user(db, row.mentee_id)
    return StatisticsOut(
        **calculate_statistics(
            tracking_start_date=account.tracking_start_date,
            today=today_local(),
            entries=entries.list_user_entries(db, row.mentee_id),
            period=period,
        )
    )

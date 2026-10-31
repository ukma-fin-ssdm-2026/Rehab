"""Private inbox API, ready for registration by the app integrator."""

from fastapi import APIRouter, Depends, Path, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, update
from backend.app.core.clock import utc_now
from backend.app.db.models.notification import Notification
from backend.app.models import ErrorResponse
from backend.app.errors import COMMON_RESPONSES
from backend.app.repositories.notifications import (
    own_notification,
    list_notifications,
    count_notifications,
)
from backend.app.schemas.notifications import (
    NotificationOut,
    NotificationList,
    SupportCommentCreate,
    SupportCommentOut,
    UnreadCount,
)
from backend.app.security import CurrentUser, get_current_user, _db_session
from backend.app.services.notifications import notification_out, send_support


def private_response(response: Response):
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    dependencies=[Depends(private_response)],
)
PRIVATE_RESPONSES = {
    **COMMON_RESPONSES,
    404: {"model": ErrorResponse, "description": "Повідомлення не знайдено"},
}
SUPPORT_RESPONSES = {
    **PRIVATE_RESPONSES,
    403: {"model": ErrorResponse, "description": "Менторство завершено"},
    409: {
        "model": ErrorResponse,
        "description": "Підтримку вже надіслано або статус запису змінено",
    },
}


class EmptyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


@router.get("", response_model=NotificationList, responses=COMMON_RESPONSES)
def inbox(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    variant: int = Query(0, ge=0, le=3),
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    return NotificationList(
        items=[
            notification_out(db, item, variant)
            for item in list_notifications(db, user.user_id, limit, offset)
        ],
        total=count_notifications(db, user.user_id),
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=UnreadCount, responses=COMMON_RESPONSES)
def unread(user: CurrentUser = Depends(get_current_user), db=Depends(_db_session)):
    return UnreadCount(count=count_notifications(db, user.user_id, unread=True))


@router.get(
    "/{notification_id}", response_model=NotificationOut, responses=PRIVATE_RESPONSES
)
def detail(
    notification_id: int = Path(..., ge=1),
    variant: int = Query(0, ge=0, le=3),
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    return notification_out(
        db, own_notification(db, user.user_id, notification_id), variant
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationOut,
    responses=PRIVATE_RESPONSES,
)
def read(
    body: EmptyBody | None = None,
    notification_id: int = Path(..., ge=1),
    variant: int = Query(0, ge=0, le=3),
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    item = own_notification(db, user.user_id, notification_id)
    db.execute(
        update(Notification)
        .where(Notification.notification_id == item.notification_id)
        .values(read_at=func.coalesce(Notification.read_at, utc_now()))
    )
    db.refresh(item)
    result = notification_out(db, item, variant)
    db.commit()
    return result


@router.post(
    "/{notification_id}/support",
    status_code=201,
    response_model=SupportCommentOut,
    responses=SUPPORT_RESPONSES,
)
def support(
    body: SupportCommentCreate,
    notification_id: int = Path(..., ge=1),
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    result = send_support(db, user.user_id, notification_id, body.text)
    db.commit()
    return result

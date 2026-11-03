# AI-GENERATED START
"""Скарга підопічного на ментора з активного або завершеного зв'язку."""

from fastapi import APIRouter, Depends

from backend.app.errors import COMMON_RESPONSES
from backend.app.models import ErrorResponse
from backend.app.schemas.complaints import ComplaintCreate, ComplaintOut
from backend.app.security import CurrentUser, _db_session, get_current_user

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "",
    status_code=201,
    response_model=ComplaintOut,
    responses={
        **COMMON_RESPONSES,
        403: {"model": ErrorResponse, "description": "Скаржитися може лише підопічний"},
        404: {
            "model": ErrorResponse,
            "description": "Зв'язок або коментар не знайдено",
        },
        409: {"model": ErrorResponse, "description": "Скарга вже розглядається"},
    },
)
def create_complaint(
    payload: ComplaintCreate,
    db=Depends(_db_session),
    user: CurrentUser = Depends(get_current_user),
) -> ComplaintOut:
    """Скаржник — власник JWT; на кого скарга, сервер бере зі зв'язку."""
    from backend.app.services.complaints import submit_complaint

    complaint = submit_complaint(db, user.user_id, payload)
    db.commit()
    return ComplaintOut.model_validate(complaint)


# AI-GENERATED END

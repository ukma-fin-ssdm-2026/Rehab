from fastapi import APIRouter, Depends, Response

from backend.app.schemas.profile import (
    ProfileOut,
    ProfilePasswordRequest,
    ProfilePreferencesRequest,
    ProfileUpdateRequest,
)
from backend.app.security import CurrentUser, _db_session, get_current_user
from backend.app.services.profile import (
    change_profile_fields,
    change_profile_password,
    change_profile_preferences,
    profile_result,
    require_profile_user,
)

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=ProfileOut)
def get_profile(
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    return profile_result(db, require_profile_user(db, user.user_id))


@router.patch("", response_model=ProfileOut)
def patch_profile(
    data: ProfileUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    return change_profile_fields(db, require_profile_user(db, user.user_id), data)


@router.put("/password", status_code=204)
def put_password(
    data: ProfilePasswordRequest,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    change_profile_password(
        db,
        require_profile_user(db, user.user_id),
        data.current_password,
        data.new_password,
    )
    return Response(status_code=204)


@router.patch("/preferences", response_model=ProfileOut)
def patch_preferences(
    data: ProfilePreferencesRequest,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    return change_profile_preferences(
        db,
        require_profile_user(db, user.user_id),
        data,
    )

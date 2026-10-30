import base64

from fastapi import APIRouter, Depends, Request, Response
from starlette.concurrency import run_in_threadpool

from backend.app.errors import api_error
from backend.app.repositories.users import lock_user_for_update

from backend.app.schemas.profile import (
    AvatarDataOut,
    AvatarUploadOut,
    ProfileOut,
    ProfilePasswordRequest,
    ProfilePreferencesRequest,
    ProfileUpdateRequest,
)
from backend.app.security import CurrentUser, _db_session, get_current_user
from backend.app.services.avatar import MAX_UPLOAD_BYTES, normalize_avatar
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


@router.put("/avatar", response_model=AvatarUploadOut)
async def put_avatar(
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    from backend.app.db.models.avatar import UserAvatar

    mime = request.headers.get("content-type", "").split(";", 1)[0].lower()
    if mime not in {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    }:
        raise api_error(422, "INVALID_AVATAR", "Непідтримуваний формат фото")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_UPLOAD_BYTES:
            raise api_error(413, "AVATAR_TOO_LARGE", "Фото перевищує 5 MiB")
        raw.extend(chunk)

    processed = await run_in_threadpool(normalize_avatar, bytes(raw))
    account = lock_user_for_update(db, user.user_id)
    if account is None:
        raise api_error(401, "UNAUTHORIZED", "Недійсна сесія")
    avatar = db.get(UserAvatar, user.user_id)
    if avatar is None:
        avatar = UserAvatar(user_id=user.user_id, image_data=processed, version=1)
        db.add(avatar)
    else:
        avatar.image_data = processed
        avatar.version += 1
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return AvatarUploadOut(has_avatar=True, avatar_version=avatar.version)


@router.get("/avatar", response_model=AvatarDataOut)
def get_avatar(
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    from backend.app.db.models.avatar import UserAvatar

    avatar = db.get(UserAvatar, user.user_id)
    if avatar is None:
        raise api_error(404, "AVATAR_NOT_FOUND", "Фото профілю відсутнє")
    response.headers["Cache-Control"] = "no-store"
    return AvatarDataOut(
        data_url="data:image/jpeg;base64," + base64.b64encode(
            avatar.image_data
        ).decode("ascii"),
        avatar_version=avatar.version,
    )


@router.delete("/avatar", status_code=204)
def delete_avatar(
    user: CurrentUser = Depends(get_current_user),
    db=Depends(_db_session),
):
    from backend.app.db.models.avatar import UserAvatar

    account = lock_user_for_update(db, user.user_id)
    if account is None:
        raise api_error(401, "UNAUTHORIZED", "Недійсна сесія")
    avatar = db.get(UserAvatar, user.user_id)
    if avatar is not None:
        db.delete(avatar)
        db.commit()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})

from backend.app.errors import api_error
from backend.app.repositories.users import get_user, revoke_sessions
from backend.app.services.auth import hash_password, verify_password


def require_profile_user(db, user_id):
    account = get_user(db, user_id)
    if account is None:
        raise api_error(401, "UNAUTHORIZED", "Недійсна або прострочена сесія")
    return account


def profile_result(db, account):
    from backend.app.db.models.avatar import UserAvatar
    from backend.app.schemas.profile import ProfileOut

    avatar = db.get(UserAvatar, account.user_id)
    return ProfileOut(
        user_id=account.user_id,
        name=account.name,
        nickname=account.nickname,
        email=account.email,
        has_avatar=avatar is not None,
        avatar_version=avatar.version if avatar is not None else None,
        email_reminders_enabled=account.email_reminders_enabled,
        message_style=account.message_style,
    )


def change_profile_fields(db, account, data):
    for field in data.model_fields_set:
        setattr(account, field, getattr(data, field))
    db.commit()
    db.refresh(account)
    return profile_result(db, account)


def change_profile_preferences(db, account, data):
    for field in data.model_fields_set:
        setattr(account, field, getattr(data, field))
    db.commit()
    db.refresh(account)
    return profile_result(db, account)


def change_profile_password(db, account, current_password, new_password):
    if not verify_password(current_password, account.password_hash):
        raise api_error(
            400,
            "CURRENT_PASSWORD_INCORRECT",
            "Неправильний поточний пароль",
        )
    if verify_password(new_password, account.password_hash):
        raise api_error(
            422,
            "PASSWORD_UNCHANGED",
            "Новий пароль має відрізнятися від поточного",
        )
    account.password_hash = hash_password(new_password)
    revoke_sessions(db, account)
    db.commit()

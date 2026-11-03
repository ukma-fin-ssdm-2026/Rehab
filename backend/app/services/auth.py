from backend.app.security import _unauthorized


def _hasher():
    from pwdlib import PasswordHash

    return PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher().hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher().verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def authenticate(db, email: str, password: str):
    from backend.app.repositories.users import get_user_by_email

    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise _unauthorized("Неправильна електронна адреса або пароль")
    return user

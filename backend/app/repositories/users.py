from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.db.models.user import User
from backend.app.core.mentor_codes import generate_mentor_code


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def lock_user_for_update(db: Session, user_id: int) -> User | None:
    """Блокує рядок користувача перед суміжними змінами в одній транзакції."""
    return db.scalar(select(User).where(User.user_id == user_id).with_for_update())


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def create_user(
    db: Session,
    *,
    name: str,
    nickname: str,
    email: str,
    password_hash: str,
    tracking_start_date,
) -> User:
    for _ in range(8):
        account = User(
            name=name,
            nickname=nickname,
            email=email.strip().lower(),
            password_hash=password_hash,
            role="user",
            tracking_start_date=tracking_start_date,
            mentor_code=generate_mentor_code(),
        )
        try:
            # A code collision must not discard the caller's other writes.
            with db.begin_nested():
                db.add(account)
                db.flush()
            return account
        except IntegrityError as error:
            constraint = getattr(
                getattr(error.orig, "diag", None), "constraint_name", None
            )
            if constraint != "uq_users_mentor_code":
                raise
    raise RuntimeError("Could not allocate a unique mentorship code")


def set_blocked(db: Session, user_id: int, blocked: bool) -> User:
    account = get_user(db, user_id)
    if account is None:
        raise LookupError("Акаунт не знайдено")
    if account.is_blocked != blocked:
        account.is_blocked = blocked
        account.token_version += 1
        db.flush()
    return account


def revoke_sessions(db: Session, account: User) -> None:
    account.token_version += 1
    db.flush()

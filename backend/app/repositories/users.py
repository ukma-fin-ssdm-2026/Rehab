from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.user import User


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def create_user(
    db: Session, *, name: str, nickname: str, email: str,
    password_hash: str, tracking_start_date,
) -> User:
    account = User(
        name=name, nickname=nickname, email=email.strip().lower(),
        password_hash=password_hash, role="user", tracking_start_date=tracking_start_date,
    )
    db.add(account)
    db.flush()
    return account


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

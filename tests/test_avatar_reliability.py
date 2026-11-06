"""Fault injection for avatar storage without blocking the request event loop."""

import asyncio
from contextlib import contextmanager
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.requests import Request
from starlette.responses import Response

from backend.app.routers import profile
from backend.app.security import CurrentUser
from backend.app.db import session as session_module
from backend.app.db.models.avatar import UserAvatar


def test_slow_avatar_database_does_not_block_other_coroutines(monkeypatch):
    started, release = Event(), Event()
    db = Mock()
    db.get.return_value = SimpleNamespace(image_data=b"old", version=4)
    monkeypatch.setattr(profile, "normalize_avatar", lambda raw: b"jpeg")

    def slow_lock(session, user_id):
        started.set()
        if not release.wait(2):
            raise RuntimeError("event loop could not release the database operation")
        return SimpleNamespace(user_id=user_id)

    monkeypatch.setattr(profile, "lock_user_for_update", slow_lock)

    async def scenario():
        async def receive():
            return {"type": "http.request", "body": b"image", "more_body": False}

        request = Request({"type": "http", "headers": [(b"content-type", b"image/png")]}, receive)
        response = Response()

        async def other_request():
            while not started.is_set():
                await asyncio.sleep(0)
            release.set()

        upload = asyncio.create_task(profile.put_avatar(
            request, response, CurrentUser(user_id=7, role="user"), db
        ))
        heartbeat = asyncio.create_task(other_request())
        try:
            result = await upload
            assert result.avatar_version == 5
            assert response.headers["cache-control"] == "no-store"
        finally:
            release.set()
            await heartbeat

    asyncio.run(scenario())


@pytest.mark.parametrize("fail_commit", [False, True])
def test_avatar_transaction_preserves_version_or_rolls_back(monkeypatch, fail_commit):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    UserAvatar.__table__.create(engine)
    with Session(engine) as seed:
        seed.add(UserAvatar(user_id=7, image_data=b"original", version=3))
        seed.commit()
    monkeypatch.setattr(session_module, "get_engine", lambda: engine)
    monkeypatch.setattr(profile, "normalize_avatar", lambda raw: b"replacement")
    monkeypatch.setattr(profile, "lock_user_for_update", lambda db, uid: object())

    async def scenario():
        async def receive():
            return {"type": "http.request", "body": b"image", "more_body": False}

        request = Request({"type": "http", "headers": [(b"content-type", b"image/png")]}, receive)
        with contextmanager(session_module.get_db)() as db:
            if fail_commit:
                def broken_commit():
                    db.flush()
                    raise RuntimeError("injected failure after database write")
                monkeypatch.setattr(db, "commit", broken_commit)
            result = await profile.put_avatar(
                request, Response(), CurrentUser(user_id=7, role="user"), db
            )
            assert result.avatar_version == 4

    try:
        if fail_commit:
            with pytest.raises(RuntimeError, match="injected failure"):
                asyncio.run(scenario())
        else:
            asyncio.run(scenario())
        with Session(engine) as check:
            saved = check.get(UserAvatar, 7)
            assert saved.version == (3 if fail_commit else 4)
            assert saved.image_data == (b"original" if fail_commit else b"replacement")
    finally:
        engine.dispose()

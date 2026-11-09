import builtins
import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.app.routers import jobs

TOKEN = "r7-test-token-at-least-thirty-two-characters"


@pytest.fixture
def broken_reminders_import(monkeypatch):
    original_import = builtins.__import__

    def inject(error):
        def fake_import(name, *args, **kwargs):
            if name == "backend.app.services.reminders":
                raise error
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

    return inject


def test_r7_valid_reminders_module_is_loaded():
    assert callable(jobs.get_reminder_creator())


def test_r7_target_module_missing_returns_specific_503(
    broken_reminders_import, caplog
):
    cause = ModuleNotFoundError(
        "No module named 'backend.app.services.reminders'",
        name="backend.app.services.reminders",
    )
    broken_reminders_import(cause)

    with caplog.at_level(logging.ERROR, logger=jobs.log.name):
        with pytest.raises(HTTPException) as caught:
            jobs.get_reminder_creator()

    assert caught.value.status_code == 503
    assert caught.value.detail["code"] == "REMINDERS_NOT_READY"
    assert caught.value.__cause__ is cause
    assert "reminders module is missing" in caplog.text


def test_r7_missing_internal_dependency_is_not_mislabelled(
    broken_reminders_import, caplog
):
    cause = ModuleNotFoundError(
        "No module named 'broken_private_dependency'",
        name="broken_private_dependency",
    )
    broken_reminders_import(cause)

    with caplog.at_level(logging.ERROR, logger=jobs.log.name):
        with pytest.raises(HTTPException) as caught:
            jobs.get_reminder_creator()

    assert caught.value.status_code == 503
    assert caught.value.detail["code"] == "REMINDERS_DEPENDENCY_ERROR"
    assert caught.value.detail["message"] == "Нагадування тимчасово недоступні"
    assert "broken_private_dependency" not in str(caught.value.detail)
    assert caught.value.__cause__ is cause
    assert "dependency module import failed" in caplog.text


def test_r7_internal_import_error_is_logged_and_safe(
    broken_reminders_import, caplog
):
    cause = ImportError("internal-private-import-error")
    broken_reminders_import(cause)

    with caplog.at_level(logging.ERROR, logger=jobs.log.name):
        with pytest.raises(HTTPException) as caught:
            jobs.get_reminder_creator()

    assert caught.value.status_code == 503
    assert caught.value.detail["code"] == "REMINDERS_DEPENDENCY_ERROR"
    assert "internal-private-import-error" not in str(caught.value.detail)
    assert caught.value.__cause__ is cause
    assert "dependency import failed" in caplog.text


def test_r7_endpoint_returns_safe_503_without_starting_job(
    broken_reminders_import, monkeypatch
):
    monkeypatch.setenv("REMINDERS_JOB_TOKEN", TOKEN)
    app = FastAPI()
    app.include_router(jobs.router)
    app.dependency_overrides[jobs.get_engine_for_job] = lambda: object()
    app.dependency_overrides[jobs.get_sender] = lambda: None
    app.dependency_overrides[jobs.get_clock] = lambda: (lambda: None)
    client = TestClient(app)
    cause = ModuleNotFoundError("hidden-private-module", name="hidden_private_module")
    broken_reminders_import(cause)

    response = client.post(
        "/internal/jobs/reminders", headers={"X-Job-Token": TOKEN}
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "REMINDERS_DEPENDENCY_ERROR"
    assert "hidden-private-module" not in response.text
    assert "REMINDERS_NOT_READY" not in response.text

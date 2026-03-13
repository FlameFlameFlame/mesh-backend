from pathlib import Path

from fastapi.testclient import TestClient

import generator.app as generator_app_mod
from app.main import create_app


class _FakeJobManager:
    def __init__(self, running: bool, allow_cancel: bool = True):
        self._running = running
        self.allow_cancel = allow_cancel
        self.cancel_calls = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def request_cancel(self) -> bool:
        self.cancel_calls += 1
        return self.allow_cancel


class _FakeWorkerThread:
    def __init__(self, alive: bool = True):
        self.alive = alive
        self.join_calls: list[float] = []

    def is_alive(self) -> bool:
        return self.alive

    def join(self, timeout: float | None = None) -> None:
        self.join_calls.append(float(timeout or 0.0))
        self.alive = False


def test_request_cancel_running_optimization_requests_cancel_and_waits(monkeypatch):
    fake_mgr = _FakeJobManager(running=True, allow_cancel=True)
    fake_thread = _FakeWorkerThread(alive=True)

    monkeypatch.setattr(generator_app_mod, "_job_manager", fake_mgr)
    monkeypatch.setattr(generator_app_mod, "_opt_thread", fake_thread)
    monkeypatch.setattr(generator_app_mod, "_opt_cancel_requested", False)

    canceled = generator_app_mod.request_cancel_running_optimization(
        reason="unit-test",
        wait_timeout_s=1.5,
    )

    assert canceled is True
    assert fake_mgr.cancel_calls == 1
    assert fake_thread.join_calls == [1.5]
    assert generator_app_mod._opt_cancel_requested is True


def test_request_cancel_running_optimization_noop_when_not_running(monkeypatch):
    fake_mgr = _FakeJobManager(running=False, allow_cancel=True)
    fake_thread = _FakeWorkerThread(alive=True)

    monkeypatch.setattr(generator_app_mod, "_job_manager", fake_mgr)
    monkeypatch.setattr(generator_app_mod, "_opt_thread", fake_thread)
    monkeypatch.setattr(generator_app_mod, "_opt_cancel_requested", False)

    canceled = generator_app_mod.request_cancel_running_optimization(
        reason="unit-test",
        wait_timeout_s=1.5,
    )

    assert canceled is False
    assert fake_mgr.cancel_calls == 0
    assert fake_thread.join_calls == []
    assert generator_app_mod._opt_cancel_requested is False


def test_app_shutdown_requests_optimization_cancel(monkeypatch, tmp_path: Path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text(
        "<!doctype html><html><body>mesh frontend</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(dist_dir))

    calls: list[dict] = []

    def _fake_cancel(**kwargs):
        calls.append(dict(kwargs))
        return True

    monkeypatch.setattr(generator_app_mod, "request_cancel_running_optimization", _fake_cancel)

    app = create_app()
    with TestClient(app):
        pass

    assert len(calls) == 1
    assert calls[0]["reason"] == "app shutdown"
    assert float(calls[0]["wait_timeout_s"]) >= 0.0


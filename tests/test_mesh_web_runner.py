import signal
import subprocess
from pathlib import Path

from app.run_web import _run_backend


class _FakeProc:
    def __init__(self, waits):
        self._waits = list(waits)
        self.sent_signals = []
        self.terminated = False
        self.killed = False
        self.pid = 4321

    def wait(self, timeout=None):
        if not self._waits:
            return 0
        event = self._waits.pop(0)
        if event == "keyboard_interrupt":
            raise KeyboardInterrupt
        if event == "timeout":
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout or 0)
        return int(event)

    def send_signal(self, sig):
        self.sent_signals.append(sig)

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


def test_run_backend_normal_exit(monkeypatch):
    fake = _FakeProc([0])
    killpg_calls = []
    monkeypatch.setattr("app.run_web.os.killpg", lambda pid, sig: killpg_calls.append((pid, sig)))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: fake)

    rc = _run_backend(["fake"], cwd=Path("."), env={})

    assert rc == 0
    assert fake.sent_signals == []
    assert killpg_calls == []


def test_run_backend_handles_ctrl_c_with_sigint(monkeypatch):
    fake = _FakeProc(["keyboard_interrupt", 0])
    killpg_calls = []
    monkeypatch.setattr("app.run_web.os.killpg", lambda pid, sig: killpg_calls.append((pid, sig)))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: fake)

    rc = _run_backend(["fake"], cwd=Path("."), env={})

    assert rc == 0
    if killpg_calls:
        assert killpg_calls == [(fake.pid, signal.SIGINT)]
        assert fake.sent_signals == []
    else:
        assert fake.sent_signals == [signal.SIGINT]


def test_run_backend_forces_kill_after_timeouts(monkeypatch):
    fake = _FakeProc(["keyboard_interrupt", "timeout", "timeout"])
    killpg_calls = []
    monkeypatch.setattr("app.run_web.os.killpg", lambda pid, sig: killpg_calls.append((pid, sig)))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: fake)

    rc = _run_backend(["fake"], cwd=Path("."), env={})

    assert rc == 130
    expected = [
        (fake.pid, signal.SIGINT),
        (fake.pid, signal.SIGTERM),
        (fake.pid, signal.SIGKILL),
    ]
    if killpg_calls:
        assert killpg_calls == expected
        assert fake.sent_signals == []
    else:
        assert fake.sent_signals == [signal.SIGINT, signal.SIGTERM, signal.SIGKILL]

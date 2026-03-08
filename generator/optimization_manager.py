import queue
import threading
from datetime import datetime, timezone
import json
import os
from typing import TextIO
from typing import Iterator


class OptimizationJobManager:
    """Manage a single in-process optimization job and its SSE event stream."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queue: queue.Queue = queue.Queue()
        self._running = False
        self._cancel_requested = False
        self._result: dict = {}
        self._log_file_path: str | None = None
        self._log_file: TextIO | None = None

    @property
    def queue(self) -> queue.Queue:
        return self._queue

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    def get_result(self) -> dict:
        with self._lock:
            return dict(self._result)

    @property
    def log_file_path(self) -> str | None:
        with self._lock:
            return self._log_file_path

    def prepare_new_job(self, log_file_path: str | None = None) -> None:
        with self._lock:
            self._result = {}
            self._cancel_requested = False
            if self._log_file is not None:
                try:
                    self._log_file.close()
                except Exception:
                    pass
                self._log_file = None
            self._log_file_path = log_file_path
            if log_file_path:
                try:
                    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                    self._log_file = open(log_file_path, "a", encoding="utf-8")
                    self._write_log_line_locked("Optimization job initialized")
                except Exception:
                    self._log_file = None
                    self._log_file_path = None
        self.drain_queue()

    def mark_running(self) -> None:
        with self._lock:
            self._running = True
            self._cancel_requested = False

    def mark_finished(self) -> None:
        with self._lock:
            self._running = False
            if self._log_file is not None:
                try:
                    self._write_log_line_locked("Optimization job finished")
                    self._log_file.close()
                except Exception:
                    pass
                self._log_file = None

    def request_cancel(self) -> bool:
        with self._lock:
            if not self._running:
                return False
            self._cancel_requested = True
            return True

    def set_result(self, result: dict) -> None:
        with self._lock:
            self._result = dict(result or {})

    def drain_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def put(self, item) -> None:
        with self._lock:
            self._write_item_log_locked(item)
        self._queue.put(item)

    def _write_log_line_locked(self, message: str) -> None:
        if self._log_file is None:
            return
        ts = datetime.now(timezone.utc).isoformat()
        self._log_file.write(f"[{ts}] {message}\n")
        self._log_file.flush()

    def _write_item_log_locked(self, item) -> None:
        if self._log_file is None:
            return
        if isinstance(item, dict):
            self._write_log_line_locked(f"EVENT {json.dumps(item, ensure_ascii=True)}")
            return
        self._write_log_line_locked(str(item))

    def iter_sse_events(self, keepalive_timeout_s: float = 30.0) -> Iterator[str]:
        while True:
            try:
                item = self._queue.get(timeout=keepalive_timeout_s)
            except queue.Empty:
                yield "data: {}\n\n"
                continue
            if isinstance(item, dict):
                import json

                yield f"data: {json.dumps(item)}\n\n"
                if item.get("done") or item.get("error") or item.get("canceled"):
                    break
            else:
                import json

                yield f"data: {json.dumps({'log': item})}\n\n"

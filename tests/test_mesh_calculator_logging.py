import logging

import generator.app  # noqa: F401  # ensure module-level logging setup runs
from generator.app import _MeshStdoutFormatter


def test_mesh_calculator_logger_streams_to_stdout_and_sse():
    logger = logging.getLogger("mesh_calculator")
    assert logger.level <= logging.INFO

    has_stdout = any(getattr(h, "_is_mesh_stdout_handler", False) for h in logger.handlers)
    has_sse = any(getattr(h, "_is_mesh_sse_handler", False) for h in logger.handlers)
    assert has_stdout
    assert has_sse


def test_mesh_stdout_formatter_humanizes_structured_payloads():
    formatter = _MeshStdoutFormatter("%(levelname)s %(name)s: %(message)s")
    record = logging.LogRecord(
        name="mesh_calculator.optimization.route_pipeline",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg={"event": "Route stats", "route_id": "route_0", "score": 0.97},
        args=(),
        exc_info=None,
    )

    rendered = formatter.format(record)
    assert "Route stats" in rendered
    assert "route_id=route_0" in rendered
    assert "score=0.97" in rendered


def test_mesh_stdout_formatter_injects_positional_args_and_strips_noise():
    formatter = _MeshStdoutFormatter("%(levelname)s %(message)s")
    record = logging.LogRecord(
        name="mesh_calculator.optimization.corridor",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg={
            "event": "Injected %d buffer cells as corridor candidates",
            "positional_args": [308],
            "level": "info",
            "logger": "mesh_calculator.optimization.corridor",
            "timestamp": "2026-03-13T20:53:09.530701Z",
        },
        args=(),
        exc_info=None,
    )

    rendered = formatter.format(record)
    assert rendered == "INFO Injected 308 buffer cells as corridor candidates"

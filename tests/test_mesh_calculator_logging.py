import logging

import generator.app  # noqa: F401  # ensure module-level logging setup runs


def test_mesh_calculator_logger_streams_to_stdout_and_sse():
    logger = logging.getLogger("mesh_calculator")
    assert logger.level <= logging.INFO

    has_stdout = any(getattr(h, "_is_mesh_stdout_handler", False) for h in logger.handlers)
    has_sse = any(getattr(h, "_is_mesh_sse_handler", False) for h in logger.handlers)
    assert has_stdout
    assert has_sse

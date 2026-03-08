from pathlib import Path

from generator.optimization_manager import OptimizationJobManager


def test_job_manager_writes_log_file(tmp_path: Path):
    log_path = tmp_path / "logs" / "optimization_test.log"

    mgr = OptimizationJobManager()
    mgr.prepare_new_job(log_file_path=str(log_path))
    mgr.mark_running()
    mgr.put("starting optimization")
    mgr.put({"progress": {"stage": "routing", "percent": 42}})
    mgr.put({"done": True, "summary": {"total_towers": 3}})
    mgr.mark_finished()

    assert log_path.is_file()
    content = log_path.read_text(encoding="utf-8")
    assert "Optimization job initialized" in content
    assert "starting optimization" in content
    assert '"progress"' in content
    assert '"done": true' in content
    assert "Optimization job finished" in content

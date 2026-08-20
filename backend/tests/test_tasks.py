import time
import pytest
from unittest.mock import patch, MagicMock
from app.tasks.manager import TaskManager


@pytest.fixture
def task_manager(app):
    with app.app_context():
        return TaskManager(app)


def test_task_manager_record_start(task_manager):
    task_manager._record_start("test-1", "discovery", {"target": "10.0.0.1"})
    task = task_manager.get_task("test-1")
    assert task is not None
    assert task["status"] == "running"
    assert task["type"] == "discovery"
    assert task["metadata"]["target"] == "10.0.0.1"
    assert task["started_at"] is not None
    assert task["completed_at"] is None


def test_task_manager_record_complete(task_manager):
    task_manager._record_start("test-2", "telemetry")
    task_manager._record_complete("test-2", {"latency": 5.0})
    task = task_manager.get_task("test-2")
    assert task["status"] == "completed"
    assert task["result"] == {"latency": 5.0}
    assert task["completed_at"] is not None


def test_task_manager_record_failure(task_manager):
    task_manager._record_start("test-3", "anomaly_detection")
    task_manager._record_failure("test-3", "something broke")
    task = task_manager.get_task("test-3")
    assert task["status"] == "failed"
    assert task["error"] == "something broke"
    assert task["completed_at"] is not None


def test_task_manager_list_tasks(task_manager):
    task_manager._record_start("t-1", "discovery")
    task_manager._record_start("t-2", "telemetry")
    task_manager._record_complete("t-2")

    all_tasks = task_manager.list_tasks()
    assert len(all_tasks) == 2

    running = task_manager.list_tasks(status="running")
    assert len(running) == 1
    assert running[0]["id"] == "t-1"

    completed = task_manager.list_tasks(status="completed")
    assert len(completed) == 1
    assert completed[0]["id"] == "t-2"


def test_task_manager_list_tasks_by_type(task_manager):
    task_manager._record_start("t-1", "discovery")
    task_manager._record_start("t-2", "telemetry")
    task_manager._record_start("t-3", "discovery")

    discovery_tasks = task_manager.list_tasks(task_type="discovery")
    assert len(discovery_tasks) == 2

    telemetry_tasks = task_manager.list_tasks(task_type="telemetry")
    assert len(telemetry_tasks) == 1


def test_task_manager_cleanup_old_tasks(task_manager):
    task_manager._record_start("old-1", "discovery")
    task_manager._record_complete("old-1")
    task_manager._record_start("old-2", "telemetry")
    task_manager._record_failure("old-2", "err")

    task = task_manager._tasks["old-1"]
    from datetime import datetime, timezone, timedelta
    old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    task["started_at"] = old_time

    task2 = task_manager._tasks["old-2"]
    task2["started_at"] = old_time

    removed = task_manager.cleanup_old_tasks(max_age_seconds=3600)
    assert removed == 2
    assert task_manager.get_task("old-1") is None
    assert task_manager.get_task("old-2") is None


def test_task_manager_cleanup_preserves_running(task_manager):
    task_manager._record_start("running-1", "discovery")
    removed = task_manager.cleanup_old_tasks(max_age_seconds=0)
    assert removed == 0
    assert task_manager.get_task("running-1") is not None


def test_task_manager_get_task_not_found(task_manager):
    assert task_manager.get_task("nonexistent") is None


def test_task_manager_list_empty(task_manager):
    tasks = task_manager.list_tasks()
    assert tasks == []


# API endpoint tests

def test_list_tasks_empty(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.get_json()
    assert "tasks" in data
    assert "count" in data
    assert isinstance(data["tasks"], list)


def test_get_task_not_found(client):
    response = client.get("/api/tasks/nonexistent-id")
    assert response.status_code == 404


def test_cleanup_tasks(client):
    response = client.post("/api/tasks/cleanup", json={
        "max_age_seconds": 0,
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "removed" in data


def test_get_scheduler_status(client):
    response = client.get("/api/tasks/scheduler")
    assert response.status_code == 200
    data = response.get_json()
    assert "scheduler_running" in data
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_telemetry_collect_all_returns_task_id(client):
    response = client.post("/api/telemetry/collect", json={})
    assert response.status_code == 202
    data = response.get_json()
    assert "task_id" in data
    assert data["task_id"].startswith("telemetry-")


def test_anomaly_detect_async_returns_task_id(client):
    response = client.post("/api/anomalies/detect", json={
        "run_async": True,
    })
    assert response.status_code == 202
    data = response.get_json()
    assert "task_id" in data
    assert data["task_id"].startswith("anomaly-")

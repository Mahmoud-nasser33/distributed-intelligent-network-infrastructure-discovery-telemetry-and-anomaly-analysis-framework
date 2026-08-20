import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List
from flask import Flask
from app.services.discovery_service import DiscoveryOrchestrator
from app.telemetry.collector import TelemetryCollector
from app.anomaly.detectors import AnomalyDetector, ThresholdDetector
from app.repositories.device_repo import DeviceRepository
from app.repositories.anomaly_repo import AnomalyRepository
from app.config.settings import Config

logger = logging.getLogger(__name__)


class TaskManager:

    def __init__(self, app: Flask = None):
        self.app = app
        self._tasks: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def _record_start(self, task_id: str, task_type: str, metadata: dict = None):
        with self._lock:
            self._tasks[task_id] = {
                "id": task_id,
                "type": task_type,
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "result": None,
                "error": None,
                "metadata": metadata or {},
            }

    def _record_complete(self, task_id: str, result=None):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["status"] = "completed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                task["result"] = result

    def _record_failure(self, task_id: str, error: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["status"] = "failed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                task["error"] = error

    def submit_discovery(self, scan_job_id: str, target: str,
                         agent_id: str = None, scan_type: str = "host",
                         providers: list = None, arguments: str = None) -> str:
        task_id = f"discovery-{scan_job_id}"
        self._record_start(task_id, "discovery", {
            "scan_job_id": scan_job_id,
            "target": target,
            "agent_id": agent_id,
            "scan_type": scan_type,
        })

        def _run():
            try:
                with self.app.app_context():
                    nmap_path = Config.NMAP_PATH
                    orch = DiscoveryOrchestrator(nmap_path=nmap_path)
                    result = orch.run_discovery(
                        scan_job_id=scan_job_id,
                        target=target,
                        agent_id=agent_id,
                        scan_type=scan_type,
                        providers=providers,
                        arguments=arguments,
                    )
                    self._record_complete(task_id, result)
            except Exception as e:
                logger.error("Discovery task %s failed: %s", task_id, str(e))
                self._record_failure(task_id, str(e))

        thread = threading.Thread(target=_run, daemon=True, name=f"task-{task_id}")
        thread.start()
        return task_id

    def submit_telemetry_collection(self, device_id: str = None) -> str:
        task_id = f"telemetry-{device_id or 'all'}"
        self._record_start(task_id, "telemetry", {
            "device_id": device_id,
        })

        def _run():
            try:
                with self.app.app_context():
                    collector = TelemetryCollector()
                    if device_id:
                        device = DeviceRepository.find_by_id(device_id)
                        if device:
                            result = collector.collect_ping_metrics(
                                device.id, device.ip_address
                            )
                            self._record_complete(task_id, result)
                        else:
                            self._record_failure(task_id, f"Device {device_id} not found")
                    else:
                        result = collector.collect_all_devices()
                        self._record_complete(task_id, {"devices_collected": len(result)})
            except Exception as e:
                logger.error("Telemetry task %s failed: %s", task_id, str(e))
                self._record_failure(task_id, str(e))

        thread = threading.Thread(target=_run, daemon=True, name=f"task-{task_id}")
        thread.start()
        return task_id

    def submit_anomaly_detection(self, device_id: str = None) -> str:
        task_id = f"anomaly-{device_id or 'all'}"
        self._record_start(task_id, "anomaly_detection", {
            "device_id": device_id,
        })

        def _run():
            try:
                with self.app.app_context():
                    detector = AnomalyDetector()
                    threshold = ThresholdDetector()
                    total_zscore = 0
                    total_threshold = 0

                    if device_id:
                        zscore_anomalies = detector.detect_and_store(device_id)
                        total_zscore += len(zscore_anomalies)
                        threshold_data = threshold.check_device(device_id)
                        for ad in threshold_data:
                            AnomalyRepository.create(ad)
                        total_threshold += len(threshold_data)
                    else:
                        from app.models.device import Device
                        devices = Device.query.filter(
                            Device.status != "offline"
                        ).all()
                        for d in devices:
                            zscore_anomalies = detector.detect_and_store(d.id)
                            total_zscore += len(zscore_anomalies)
                            threshold_data = threshold.check_device(d.id)
                            for ad in threshold_data:
                                AnomalyRepository.create(ad)
                            total_threshold += len(threshold_data)

                    self._record_complete(task_id, {
                        "zscore_anomalies": total_zscore,
                        "threshold_anomalies": total_threshold,
                        "total": total_zscore + total_threshold,
                    })
            except Exception as e:
                logger.error("Anomaly detection task %s failed: %s", task_id, str(e))
                self._record_failure(task_id, str(e))

        thread = threading.Thread(target=_run, daemon=True, name=f"task-{task_id}")
        thread.start()
        return task_id

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self, task_type: str = None, status: str = None) -> List[dict]:
        with self._lock:
            tasks = list(self._tasks.values())
        if task_type:
            tasks = [t for t in tasks if t["type"] == task_type]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return sorted(tasks, key=lambda t: t["started_at"], reverse=True)

    def cleanup_old_tasks(self, max_age_seconds: int = 3600) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_seconds
        removed = 0
        with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task["status"] in ("completed", "failed"):
                    try:
                        started = datetime.fromisoformat(
                            task["started_at"]
                        ).timestamp()
                        if started < cutoff:
                            to_remove.append(task_id)
                    except (ValueError, KeyError):
                        pass
            for task_id in to_remove:
                del self._tasks[task_id]
                removed += 1
        return removed

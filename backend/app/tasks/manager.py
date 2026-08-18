import logging
import threading
from typing import Optional
from flask import Flask
from app.services.discovery_service import DiscoveryOrchestrator
from app.telemetry.collector import TelemetryCollector
from app.anomaly.detectors import AnomalyDetector, ThresholdDetector
from app.repositories.device_repo import DeviceRepository

logger = logging.getLogger(__name__)


class TaskManager:

    def __init__(self, app: Flask = None):
        self.app = app
        self._running_tasks = {}

    def submit_discovery(self, scan_job_id: str, target: str,
                         agent_id: str = None, scan_type: str = "host",
                         providers: list = None, arguments: str = None) -> str:
        task_id = f"discovery-{scan_job_id}"
        self._running_tasks[task_id] = {"status": "running", "type": "discovery"}

        def _run():
            try:
                with self.app.app_context():
                    orch = DiscoveryOrchestrator()
                    result = orch.run_discovery(
                        scan_job_id=scan_job_id,
                        target=target,
                        agent_id=agent_id,
                        scan_type=scan_type,
                        providers=providers,
                        arguments=arguments,
                    )
                    self._running_tasks[task_id] = {"status": "completed", "result": result}
            except Exception as e:
                logger.error("Discovery task %s failed: %s", task_id, str(e))
                self._running_tasks[task_id] = {"status": "failed", "error": str(e)}

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return task_id

    def submit_telemetry_collection(self, device_id: str = None) -> str:
        task_id = f"telemetry-{device_id or 'all'}"
        self._running_tasks[task_id] = {"status": "running", "type": "telemetry"}

        def _run():
            try:
                with self.app.app_context():
                    collector = TelemetryCollector()
                    if device_id:
                        device = DeviceRepository.find_by_id(device_id)
                        if device:
                            collector.collect_ping_metrics(device.id, device.ip_address)
                    else:
                        collector.collect_all_devices()
                    self._running_tasks[task_id] = {"status": "completed"}
            except Exception as e:
                logger.error("Telemetry task %s failed: %s", task_id, str(e))
                self._running_tasks[task_id] = {"status": "failed", "error": str(e)}

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return task_id

    def submit_anomaly_detection(self, device_id: str = None) -> str:
        task_id = f"anomaly-{device_id or 'all'}"
        self._running_tasks[task_id] = {"status": "running", "type": "anomaly_detection"}

        def _run():
            try:
                with self.app.app_context():
                    detector = AnomalyDetector()
                    threshold = ThresholdDetector()
                    if device_id:
                        detector.detect_and_store(device_id)
                        threshold_data = threshold.check_device(device_id)
                    else:
                        from app.models.device import Device
                        devices = Device.query.filter(Device.status != "offline").all()
                        for d in devices:
                            detector.detect_and_store(d.id)
                            threshold.check_device(d.id)
                    self._running_tasks[task_id] = {"status": "completed"}
            except Exception as e:
                logger.error("Anomaly detection task %s failed: %s", task_id, str(e))
                self._running_tasks[task_id] = {"status": "failed", "error": str(e)}

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return task_id

    def get_task_status(self, task_id: str) -> Optional[dict]:
        return self._running_tasks.get(task_id)

    def list_tasks(self) -> dict:
        return self._running_tasks

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask

logger = logging.getLogger(__name__)


class TaskScheduler:

    def __init__(self, app: Flask = None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        self._started = False

    def init_app(self, app: Flask):
        self.app = app
        config = app.config

        self.scheduler.add_job(
            self._run_telemetry_collection,
            trigger=IntervalTrigger(
                seconds=config.get("SCHEDULER_TELEMETRY_INTERVAL", 300),
            ),
            id="periodic_telemetry",
            name="Periodic telemetry collection",
            replace_existing=True,
        )

        self.scheduler.add_job(
            self._run_anomaly_detection,
            trigger=IntervalTrigger(
                seconds=config.get("SCHEDULER_ANOMALY_INTERVAL", 600),
            ),
            id="periodic_anomaly_detection",
            name="Periodic anomaly detection",
            replace_existing=True,
        )

        self.scheduler.add_job(
            self._cleanup_tasks,
            trigger=IntervalTrigger(
                seconds=config.get("SCHEDULER_CLEANUP_INTERVAL", 1800),
            ),
            id="periodic_task_cleanup",
            name="Periodic task cleanup",
            replace_existing=True,
        )

        logger.info(
            "Task scheduler configured: telemetry=%ds, anomaly=%ds, cleanup=%ds",
            config.get("SCHEDULER_TELEMETRY_INTERVAL", 300),
            config.get("SCHEDULER_ANOMALY_INTERVAL", 600),
            config.get("SCHEDULER_CLEANUP_INTERVAL", 1800),
        )

    def start(self):
        if not self._started and not self.scheduler.running:
            self.scheduler.start()
            self._started = True
            logger.info("Task scheduler started")

    def shutdown(self):
        if self._started and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Task scheduler stopped")

    def get_jobs(self):
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": (
                    job.next_run_time.isoformat()
                    if job.next_run_time else None
                ),
                "trigger": str(job.trigger),
            })
        return jobs

    def _run_telemetry_collection(self):
        with self.app.app_context():
            try:
                self.app.task_manager.submit_telemetry_collection()
                logger.info("Scheduled telemetry collection triggered")
            except Exception as e:
                logger.error("Scheduled telemetry failed: %s", str(e))

    def _run_anomaly_detection(self):
        with self.app.app_context():
            try:
                self.app.task_manager.submit_anomaly_detection()
                logger.info("Scheduled anomaly detection triggered")
            except Exception as e:
                logger.error("Scheduled anomaly detection failed: %s", str(e))

    def _cleanup_tasks(self):
        with self.app.app_context():
            try:
                removed = self.app.task_manager.cleanup_old_tasks()
                if removed:
                    logger.info("Cleaned up %d old tasks", removed)
            except Exception as e:
                logger.error("Task cleanup failed: %s", str(e))

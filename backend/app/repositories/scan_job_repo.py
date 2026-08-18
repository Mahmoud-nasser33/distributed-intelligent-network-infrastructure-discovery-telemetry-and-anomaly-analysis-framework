from typing import List, Optional
from datetime import datetime, timezone
from app.config.database import db
from app.models.discovery import ScanJob, ScanJobStatus


class ScanJobRepository:

    @staticmethod
    def create(data: dict) -> ScanJob:
        job = ScanJob(
            agent_id=data.get("agent_id"),
            target=data["target"],
            scan_type=data.get("scan_type", "discovery"),
            scan_arguments=data.get("scan_arguments"),
            status="pending",
        )
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def find_by_id(job_id: str) -> Optional[ScanJob]:
        return ScanJob.query.get(job_id)

    @staticmethod
    def find_all(status: str = None, agent_id: str = None) -> List[ScanJob]:
        query = ScanJob.query
        if status:
            query = query.filter_by(status=status)
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        return query.order_by(ScanJob.created_at.desc()).all()

    @staticmethod
    def update_status(job_id: str, status: str, **kwargs) -> Optional[ScanJob]:
        job = ScanJob.query.get(job_id)
        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            if status == "running" and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            elif status in ("completed", "failed", "partial"):
                job.completed_at = datetime.now(timezone.utc)
            db.session.commit()
        return job

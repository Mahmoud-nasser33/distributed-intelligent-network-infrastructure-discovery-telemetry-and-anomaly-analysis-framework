from typing import List, Optional
from datetime import datetime, timezone
from app.config.database import db
from app.models.observation import Observation


class ObservationRepository:

    @staticmethod
    def create(data: dict) -> Observation:
        obs = Observation(
            agent_id=data.get("agent_id"),
            scan_job_id=data.get("scan_job_id"),
            source=data["source"],
            target_ip=data["target_ip"],
            target_mac=data.get("target_mac"),
            observation_type=data["observation_type"],
            raw_data=data.get("raw_data"),
            normalized_data=data.get("normalized_data"),
            confidence=data.get("confidence"),
            device_id=data.get("device_id"),
        )
        db.session.add(obs)
        db.session.commit()
        return obs

    @staticmethod
    def find_by_device(device_id: str, limit: int = 100) -> List[Observation]:
        return Observation.query.filter_by(device_id=device_id)\
            .order_by(Observation.timestamp.desc()).limit(limit).all()

    @staticmethod
    def find_by_scan_job(scan_job_id: str) -> List[Observation]:
        return Observation.query.filter_by(scan_job_id=scan_job_id)\
            .order_by(Observation.timestamp.desc()).all()

    @staticmethod
    def find_by_target(ip_address: str, limit: int = 50) -> List[Observation]:
        return Observation.query.filter_by(target_ip=ip_address)\
            .order_by(Observation.timestamp.desc()).limit(limit).all()

    @staticmethod
    def find_recent(limit: int = 100) -> List[Observation]:
        return Observation.query.order_by(
            Observation.timestamp.desc()
        ).limit(limit).all()

    @staticmethod
    def count_all() -> int:
        return Observation.query.count()

    @staticmethod
    def update_device_id(observation_id: str, device_id: str) -> Optional[Observation]:
        obs = Observation.query.get(observation_id)
        if obs:
            obs.device_id = device_id
            db.session.commit()
        return obs

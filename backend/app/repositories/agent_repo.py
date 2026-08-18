from typing import List, Optional
from datetime import datetime, timezone
from app.config.database import db
from app.models.agent import Agent


class AgentRepository:

    @staticmethod
    def register(name: str, agent_type: str, data: dict) -> Agent:
        agent = Agent.query.filter_by(name=name, agent_type=agent_type).first()
        now = datetime.now(timezone.utc)

        if agent:
            agent.ip_address = data.get("ip_address", agent.ip_address)
            agent.version = data.get("version", agent.version)
            agent.network_scope = data.get("network_scope", agent.network_scope)
            agent.description = data.get("description", agent.description)
            agent.status = "active"
            agent.last_seen = now
            agent.last_heartbeat = now
        else:
            agent = Agent(
                name=name,
                agent_type=agent_type,
                ip_address=data.get("ip_address"),
                version=data.get("version"),
                network_scope=data.get("network_scope"),
                description=data.get("description"),
                status="active",
                last_heartbeat=now,
                last_seen=now,
            )
            db.session.add(agent)

        db.session.commit()
        return agent

    @staticmethod
    def heartbeat(agent_id: str, data: dict = None) -> Optional[Agent]:
        agent = Agent.query.get(agent_id)
        if agent:
            now = datetime.now(timezone.utc)
            agent.last_heartbeat = now
            agent.last_seen = now
            agent.status = "active"
            if data:
                if "ip_address" in data:
                    agent.ip_address = data["ip_address"]
                if "version" in data:
                    agent.version = data["version"]
            db.session.commit()
        return agent

    @staticmethod
    def find_by_id(agent_id: str) -> Optional[Agent]:
        return Agent.query.get(agent_id)

    @staticmethod
    def find_all(status: str = None) -> List[Agent]:
        query = Agent.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Agent.last_seen.desc()).all()

    @staticmethod
    def find_stale(timeout_seconds: int = 90) -> List[Agent]:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        return Agent.query.filter(
            Agent.last_heartbeat < cutoff,
            Agent.status == "active"
        ).all()

    @staticmethod
    def mark_stale(agent_ids: List[str]):
        for aid in agent_ids:
            agent = Agent.query.get(aid)
            if agent:
                agent.status = "stale"
        db.session.commit()

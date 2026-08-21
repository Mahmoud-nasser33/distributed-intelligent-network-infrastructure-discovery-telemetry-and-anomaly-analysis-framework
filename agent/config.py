import os
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    server_url: str = "http://localhost:5000"
    name: str = ""
    network_scope: str = ""
    collect_interval: int = 60
    heartbeat_interval: int = 30
    ping_count: int = 2
    ping_timeout_ms: int = 2000
    max_workers: int = 20
    request_timeout: int = 10

    @classmethod
    def from_env(cls):
        return cls(
            server_url=os.environ.get("DINAS_SERVER_URL", cls.server_url),
            name=os.environ.get("DINAS_AGENT_NAME", ""),
            network_scope=os.environ.get("DINAS_NETWORK_SCOPE", ""),
            collect_interval=int(os.environ.get("DINAS_COLLECT_INTERVAL", cls.collect_interval)),
            heartbeat_interval=int(os.environ.get("DINAS_HEARTBEAT_INTERVAL", cls.heartbeat_interval)),
            ping_count=int(os.environ.get("DINAS_PING_COUNT", cls.ping_count)),
            max_workers=int(os.environ.get("DINAS_MAX_WORKERS", cls.max_workers)),
        )

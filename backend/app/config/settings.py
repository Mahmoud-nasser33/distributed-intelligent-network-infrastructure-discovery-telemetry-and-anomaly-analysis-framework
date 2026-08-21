import os
from pathlib import Path

basedir = Path(__file__).resolve().parent.parent.parent


class Config:
    SECRET_KEY = os.environ.get("DINAS_SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DINAS_DATABASE_URL",
        f"sqlite:///{basedir / 'instance' / 'dinas.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DINAS_LOG_LEVEL = os.environ.get("DINAS_LOG_LEVEL", "INFO")
    DINAS_LOG_DIR = os.environ.get("DINAS_LOG_DIR", str(basedir / "logs"))

    NMAP_PATH = os.environ.get("NMAP_PATH", "nmap")
    SNMP_COMMUNITY = os.environ.get("SNMP_COMMUNITY", "public")

    AGENT_HEARTBEAT_INTERVAL = int(os.environ.get("AGENT_HEARTBEAT_INTERVAL", "30"))
    AGENT_TIMEOUT = int(os.environ.get("AGENT_TIMEOUT", "90"))
    AGENT_COLLECT_INTERVAL = int(os.environ.get("AGENT_COLLECT_INTERVAL", "60"))
    AGENT_PING_COUNT = int(os.environ.get("AGENT_PING_COUNT", "2"))

    DISCOVERY_TIMEOUT = int(os.environ.get("DISCOVERY_TIMEOUT", "300"))
    DISCOVERY_MAX_CONCURRENT = int(os.environ.get("DISCOVERY_MAX_CONCURRENT", "5"))

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    ANOMALY_LATENCY_THRESHOLD = float(os.environ.get("ANOMALY_LATENCY_THRESHOLD", "3.0"))
    ANOMALY_MIN_SAMPLES = int(os.environ.get("ANOMALY_MIN_SAMPLES", "10"))

    TOPOLOGY_PING_TIMEOUT = int(os.environ.get("TOPOLOGY_PING_TIMEOUT", "2"))
    TOPOLOGY_MAX_CONCURRENT = int(os.environ.get("TOPOLOGY_MAX_CONCURRENT", "10"))
    TOPOLOGY_TRACEROUTE_HOPS = int(os.environ.get("TOPOLOGY_TRACEROUTE_HOPS", "15"))
    TOPOLOGY_TRACEROUTE_TIMEOUT = int(os.environ.get("TOPOLOGY_TRACEROUTE_TIMEOUT", "5"))

    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_TELEMETRY_INTERVAL = int(os.environ.get("SCHEDULER_TELEMETRY_INTERVAL", "300"))
    SCHEDULER_ANOMALY_INTERVAL = int(os.environ.get("SCHEDULER_ANOMALY_INTERVAL", "600"))
    SCHEDULER_CLEANUP_INTERVAL = int(os.environ.get("SCHEDULER_CLEANUP_INTERVAL", "1800"))
    SCHEDULER_AGENT_HEALTH_INTERVAL = int(os.environ.get("SCHEDULER_AGENT_HEALTH_INTERVAL", "60"))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

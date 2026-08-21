import logging
import socket
import threading
import time
from typing import Optional

from agent import __version__
from agent.collector import PingCollector
from agent.config import AgentConfig
from agent.server_client import ServerClient, ServerError

logger = logging.getLogger(__name__)


class DinasAgent:
    """Registers with the server, sends heartbeats, collects and pushes telemetry."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = ServerClient(config.server_url, config.request_timeout)
        self.collector = PingCollector(
            ping_count=config.ping_count,
            timeout_ms=config.ping_timeout_ms,
            max_workers=config.max_workers,
        )
        self.agent_id: Optional[str] = None
        self._stop_event = threading.Event()
        self._heartbeat_thread: Optional[threading.Thread] = None

    def run(self):
        logger.info("DINAS agent %s starting (server=%s)",
                    self.config.name or "(unnamed)", self.config.server_url)
        self._register()

        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, name="heartbeat", daemon=True,
        )
        self._heartbeat_thread.start()

        try:
            self._collect_loop()
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self._stop_event.set()

    def stop(self):
        self._stop_event.set()

    def _register(self):
        payload = {
            "name": self.config.name,
            "agent_type": "telemetry",
            "version": __version__,
            "ip_address": self._local_ip(),
            "network_scope": self.config.network_scope or None,
            "description": f"DINAS agent on {socket.gethostname()}",
        }

        try:
            data = self.client.register(payload)
        except ServerError as e:
            raise SystemExit(f"Registration failed: {e}")

        self.agent_id = data["agent"]["id"]
        logger.info("Registered with server as '%s' (id=%s)",
                    payload["name"], self.agent_id)

    def _reregister(self):
        logger.warning("Agent no longer known to server, re-registering")
        self._register()

    def _heartbeat_loop(self):
        while not self._stop_event.wait(self.config.heartbeat_interval):
            try:
                self.client.heartbeat(self.agent_id, {
                    "ip_address": self._local_ip(),
                    "version": __version__,
                })
                logger.debug("Heartbeat sent")
            except ServerError as e:
                logger.error("Heartbeat failed: %s", e)
                if "Not found" in str(e):
                    try:
                        self._reregister()
                    except SystemExit as exc:
                        logger.error("Re-registration failed: %s", exc)
                        return

    def _collect_loop(self):
        while not self._stop_event.is_set():
            started = time.monotonic()
            try:
                self._collect_once()
            except Exception as e:
                logger.error("Collection cycle failed: %s", e)

            elapsed = time.monotonic() - started
            wait = max(1.0, self.config.collect_interval - elapsed)
            self._stop_event.wait(wait)

    def _collect_once(self):
        targets = self.collector.scope_targets(self.config.network_scope)
        if not targets:
            logger.warning("No valid targets in scope '%s', skipping cycle",
                           self.config.network_scope)
            return

        logger.info("Collecting telemetry for %d target(s)", len(targets))
        results = self.collector.collect(targets)

        online = sum(1 for r in results if r["status"] == "online")
        logger.info("Collection done: %d/%d online", online, len(results))

        try:
            data = self.client.submit_telemetry(self.agent_id, results)
            logger.info("Server stored %d metric(s)", data.get("stored", 0))
        except ServerError as e:
            logger.error("Telemetry submission failed: %s", e)
            if "Not found" in str(e):
                self._reregister()

    @staticmethod
    def _local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
            finally:
                s.close()
        except OSError:
            return "127.0.0.1"

import logging
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class ServerError(Exception):
    pass


class ServerClient:
    """HTTP client for talking to the DINAS server."""

    def __init__(self, server_url: str, request_timeout: int = 10):
        self.server_url = server_url.rstrip("/")
        self.request_timeout = request_timeout
        self.session = requests.Session()

    def register(self, payload: Dict) -> Dict:
        return self._request("POST", "/api/agents/register", json=payload)

    def heartbeat(self, agent_id: str, payload: Dict = None) -> Dict:
        return self._request(
            "POST", f"/api/agents/{agent_id}/heartbeat", json=payload or {}
        )

    def submit_telemetry(self, agent_id: str, results: list) -> Dict:
        return self._request(
            "POST", f"/api/agents/{agent_id}/telemetry",
            json={"results": results},
        )

    def get_config(self, agent_id: str) -> Dict:
        return self._request("GET", f"/api/agents/{agent_id}/config")

    def _request(self, method: str, path: str, json: Dict = None) -> Dict:
        url = f"{self.server_url}{path}"
        try:
            response = self.session.request(
                method, url, json=json, timeout=self.request_timeout,
            )
        except requests.RequestException as e:
            raise ServerError(f"Cannot reach server at {url}: {e}") from e

        if response.status_code == 404:
            raise ServerError(f"Not found on server: {path}")

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code >= 400:
            message = data.get("error", f"HTTP {response.status_code}")
            raise ServerError(f"Server rejected {method} {path}: {message}")

        return data

    def find_agent_by_name(self, name: str) -> Optional[Dict]:
        try:
            data = self._request("GET", "/api/agents")
        except ServerError:
            return None
        for agent in data.get("agents", []):
            if agent.get("name") == name:
                return agent
        return None

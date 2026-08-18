import subprocess
import shutil
import logging
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from app.discovery.base import DiscoveryProvider, DiscoveryResult
from app.services.classifier import DeviceClassifier

logger = logging.getLogger(__name__)


class NmapDiscoveryProvider(DiscoveryProvider):

    def __init__(self, nmap_path: str = "nmap"):
        self.nmap_path = nmap_path
        self.classifier = DeviceClassifier()

    @property
    def name(self) -> str:
        return "nmap"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.nmap_path, "--version"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def discover_host(self, target: str, **kwargs) -> Optional[DiscoveryResult]:
        arguments = kwargs.get("arguments", "-sV -O -T4 --host-timeout 60s")
        args_list = arguments.split()
        cmd = [self.nmap_path] + args_list + [target, "-oX", "-"]

        logger.info("Executing nmap: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=kwargs.get("timeout", 300),
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            if result.returncode != 0:
                logger.error("Nmap failed for %s: %s", target, result.stderr)
                return None

            return self._parse_xml_output(result.stdout, target)

        except subprocess.TimeoutExpired:
            logger.warning("Nmap timed out for target: %s", target)
            return None
        except Exception as e:
            logger.error("Nmap execution error for %s: %s", target, str(e))
            return None

    def discover_network(self, network_range: str, **kwargs) -> List[DiscoveryResult]:
        arguments = kwargs.get("arguments", "-sn -T4 --host-timeout 30s")
        args_list = arguments.split()
        cmd = [self.nmap_path] + args_list + [network_range, "-oX", "-"]

        logger.info("Executing network discovery: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=kwargs.get("timeout", 600),
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            if result.returncode != 0:
                logger.error("Nmap network discovery failed: %s", result.stderr)
                return []

            return self._parse_network_xml(result.stdout)

        except subprocess.TimeoutExpired:
            logger.warning("Nmap network discovery timed out for: %s", network_range)
            return []
        except Exception as e:
            logger.error("Nmap network discovery error: %s", str(e))
            return []

    def _parse_xml_output(self, xml_output: str, target: str) -> Optional[DiscoveryResult]:
        try:
            root = ET.fromstring(xml_output)
            host_elem = root.find(".//host")
            if host_elem is None:
                return None

            status_elem = host_elem.find("status")
            if status_elem is not None and status_elem.get("state") != "up":
                return None

            ip_address = target
            mac_address = None
            vendor = None

            for addr_elem in host_elem.findall("address"):
                if addr_elem.get("addrtype") == "ipv4":
                    ip_address = addr_elem.get("addr")
                elif addr_elem.get("addrtype") == "mac":
                    mac_address = addr_elem.get("addr")
                    vendor = addr_elem.get("vendor")

            hostname = None
            hostname_elem = host_elem.find(".//hostname")
            if hostname_elem is not None:
                hostname = hostname_elem.get("name")

            os_detection = None
            os_confidence = None
            os_matches = host_elem.findall(".//osmatch")
            if os_matches:
                best_match = os_matches[0]
                os_detection = best_match.get("name")
                os_confidence = float(best_match.get("accuracy", 0)) / 100.0

            services = []
            for port_elem in host_elem.findall(".//port"):
                state_elem = port_elem.find("state")
                service_elem = port_elem.find("service")
                service_info = {
                    "port": int(port_elem.get("portid", 0)),
                    "protocol": port_elem.get("protocol", "tcp"),
                    "state": state_elem.get("state", "unknown") if state_elem is not None else "unknown",
                    "service_name": service_elem.get("name") if service_elem is not None else None,
                    "version": self._build_version(service_elem) if service_elem is not None else None,
                    "product": service_elem.get("product") if service_elem is not None else None,
                    "confidence": float(service_elem.get("conf", 0)) / 100.0 if service_elem is not None and service_elem.get("conf") else None,
                }
                services.append(service_info)

            interfaces = []
            ip_info = host_elem.find(".//address[@addrtype='ipv4']")
            if ip_info is not None:
                interfaces.append({
                    "name": "eth0",
                    "ip_address": ip_info.get("addr"),
                    "is_up": True,
                })

            classification = self.classifier.classify(
                mac_address=mac_address,
                vendor=vendor,
                hostname=hostname,
                os_detection=os_detection,
                os_confidence=os_confidence,
                services=services,
            )

            raw_data = {
                "xml_output": xml_output,
                "nmap_version": root.get("scanner", ""),
                "args": root.get("args", ""),
            }

            return DiscoveryResult(
                ip_address=ip_address,
                mac_address=mac_address,
                hostname=hostname,
                vendor=vendor,
                os_detection=os_detection,
                os_confidence=os_confidence,
                device_type=classification.get("device_type"),
                classification_confidence=classification.get("confidence"),
                services=services,
                interfaces=interfaces,
                raw_data=raw_data,
            )

        except ET.ParseError as e:
            logger.error("Failed to parse Nmap XML: %s", str(e))
            return None

    def _parse_network_xml(self, xml_output: str) -> List[DiscoveryResult]:
        results = []
        try:
            root = ET.fromstring(xml_output)
            for host_elem in root.findall(".//host"):
                status_elem = host_elem.find("status")
                if status_elem is not None and status_elem.get("state") != "up":
                    continue

                ip_address = None
                mac_address = None
                vendor = None

                for addr_elem in host_elem.findall("address"):
                    if addr_elem.get("addrtype") == "ipv4":
                        ip_address = addr_elem.get("addr")
                    elif addr_elem.get("addrtype") == "mac":
                        mac_address = addr_elem.get("addr")
                        vendor = addr_elem.get("vendor")

                if not ip_address:
                    continue

                hostname = None
                hostname_elem = host_elem.find(".//hostname")
                if hostname_elem is not None:
                    hostname = hostname_elem.get("name")

                classification = self.classifier.classify(
                    mac_address=mac_address,
                    vendor=vendor,
                    hostname=hostname,
                )

                results.append(DiscoveryResult(
                    ip_address=ip_address,
                    mac_address=mac_address,
                    hostname=hostname,
                    vendor=vendor,
                    device_type=classification.get("device_type"),
                    classification_confidence=classification.get("confidence"),
                ))

        except ET.ParseError as e:
            logger.error("Failed to parse network scan XML: %s", str(e))

        return results

    def _build_version(self, service_elem) -> str:
        if service_elem is None:
            return None
        parts = []
        if service_elem.get("product"):
            parts.append(service_elem.get("product"))
        if service_elem.get("version"):
            parts.append(service_elem.get("version"))
        return " ".join(parts) if parts else None

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

VENDOR_DEVICE_HINTS = {
    "cisco": "router",
    "juniper": "router",
    "mikrotik": "router",
    "ubiquiti": "access_point",
    "aruba": "access_point",
    "hp": "switch",
    "dell": "server",
    "lenovo": "desktop",
    "apple": "desktop",
    "samsung": "mobile",
    "tp-link": "access_point",
    "netgear": "switch",
    "fortinet": "firewall",
    "paloalto": "firewall",
    "sonicwall": "firewall",
}

PORT_DEVICE_HINTS = {
    22: "server",
    80: "server",
    443: "server",
    3389: "desktop",
    445: "server",
    23: None,
    9100: "printer",
    631: "printer",
    161: None,
    8080: "server",
}


class DeviceClassifier:

    def classify(self, mac_address: str = None, vendor: str = None,
                 hostname: str = None, os_detection: str = None,
                 os_confidence: float = None,
                 services: List[Dict] = None) -> Dict[str, Any]:
        scores = {}

        if vendor:
            vendor_lower = vendor.lower()
            for hint_vendor, device_type in VENDOR_DEVICE_HINTS.items():
                if hint_vendor in vendor_lower:
                    scores[device_type] = scores.get(device_type, 0) + 0.4
                    break

        if services:
            port_counts = {}
            for svc in services:
                port = svc.get("port")
                if port in PORT_DEVICE_HINTS:
                    hint_type = PORT_DEVICE_HINTS[port]
                    if hint_type:
                        port_counts[hint_type] = port_counts.get(hint_type, 0) + 1

            for device_type, count in port_counts.items():
                scores[device_type] = scores.get(device_type, 0) + (0.2 * min(count, 3))

        if hostname:
            hostname_lower = hostname.lower()
            if any(x in hostname_lower for x in ["router", "gw", "gateway"]):
                scores["router"] = scores.get("router", 0) + 0.3
            elif any(x in hostname_lower for x in ["switch", "sw"]):
                scores["switch"] = scores.get("switch", 0) + 0.3
            elif any(x in hostname_lower for x in ["firewall", "fw", "utm"]):
                scores["firewall"] = scores.get("firewall", 0) + 0.3
            elif any(x in hostname_lower for x in ["server", "srv", "web"]):
                scores["server"] = scores.get("server", 0) + 0.3
            elif any(x in hostname_lower for x in ["printer", "print"]):
                scores["printer"] = scores.get("printer", 0) + 0.3
            elif any(x in hostname_lower for x in ["ap", "wifi", "wireless"]):
                scores["access_point"] = scores.get("access_point", 0) + 0.3
            elif any(x in hostname_lower for x in ["iot", "sensor", "camera"]):
                scores["iot"] = scores.get("iot", 0) + 0.3

        if os_detection:
            os_lower = os_detection.lower()
            if any(x in os_lower for x in ["windows"]):
                scores["desktop"] = scores.get("desktop", 0) + 0.2
            elif any(x in os_lower for x in ["linux", "ubuntu", "centos", "debian"]):
                scores["server"] = scores.get("server", 0) + 0.2
            elif any(x in os_lower for x in ["ios", "cisco"]):
                scores["router"] = scores.get("router", 0) + 0.2

        if not scores:
            return {"device_type": "unknown", "confidence": 0.0}

        best_type = max(scores, key=scores.get)
        raw_confidence = min(scores[best_type], 1.0)

        return {
            "device_type": best_type,
            "confidence": round(raw_confidence, 2),
        }

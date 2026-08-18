import logging
from typing import List, Optional
from app.topology.discovery.base import TopologyDiscoveryProvider, TopologyEdgeResult
from app.models.device import Device, NetworkInterface

logger = logging.getLogger(__name__)


class SubnetAdjacencyProvider(TopologyDiscoveryProvider):

    @property
    def name(self) -> str:
        return "subnet_adjacency"

    @property
    def edge_type(self) -> str:
        return "subnet_adjacent"

    @property
    def default_confidence(self) -> float:
        return 0.6

    def is_available(self) -> bool:
        return True

    def discover(self, device_ips: List[str], **kwargs) -> List[TopologyEdgeResult]:
        ip_set = set(device_ips)
        devices = Device.query.filter(
            Device.ip_address.in_(device_ips),
            Device.status != "offline",
        ).all()

        subnet_groups = {}
        for device in devices:
            subnets = self._get_device_subnets(device)
            for subnet in subnets:
                if subnet not in subnet_groups:
                    subnet_groups[subnet] = []
                subnet_groups[subnet].append(device)

        edges = []
        seen_pairs = set()

        for subnet, subnet_devices in subnet_groups.items():
            if len(subnet_devices) < 2:
                continue
            for i in range(len(subnet_devices)):
                for j in range(i + 1, len(subnet_devices)):
                    dev_a = subnet_devices[i]
                    dev_b = subnet_devices[j]
                    pair_key = tuple(sorted([dev_a.id, dev_b.id]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    evidence = {
                        "shared_subnet": subnet,
                        "device_a_ip": dev_a.ip_address,
                        "device_b_ip": dev_b.ip_address,
                    }
                    edges.append(TopologyEdgeResult(
                        source_ip=dev_a.ip_address,
                        destination_ip=dev_b.ip_address,
                        edge_type=self.edge_type,
                        confidence=self.default_confidence,
                        evidence=evidence,
                        metadata={"provider": self.name},
                    ))

        logger.info("Subnet adjacency discovery found %d edges from %d devices",
                     len(edges), len(device_ips))
        return edges

    def _get_device_subnets(self, device: Device) -> List[str]:
        subnets = []
        for iface in device.interfaces.all():
            if iface.ip_address and iface.subnet_mask:
                subnet = self._calculate_subnet(iface.ip_address, iface.subnet_mask)
                if subnet:
                    subnets.append(subnet)

        if not subnets and device.ip_address:
            parts = device.ip_address.split(".")
            if len(parts) == 4:
                subnets.append(f"{parts[0]}.{parts[1]}.{parts[2]}.0/24")

        return subnets

    def _calculate_subnet(self, ip_address: str, subnet_mask: str) -> Optional[str]:
        try:
            ip_parts = [int(p) for p in ip_address.split(".")]
            mask_parts = [int(p) for p in subnet_mask.split(".")]
            network_parts = [ip_parts[i] & mask_parts[i] for i in range(4)]
            cidr = sum(bin(m).count('1') for m in mask_parts)
            return f"{network_parts[0]}.{network_parts[1]}.{network_parts[2]}.{network_parts[3]}/{cidr}"
        except (ValueError, IndexError):
            return None

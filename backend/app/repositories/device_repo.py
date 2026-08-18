from typing import List, Optional
from datetime import datetime, timezone
from app.config.database import db
from app.models.device import Device, NetworkInterface, Service


class DeviceRepository:

    @staticmethod
    def find_by_ip(ip_address: str, agent_id: str = None) -> Optional[Device]:
        query = Device.query.filter_by(ip_address=ip_address)
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        return query.first()

    @staticmethod
    def find_by_id(device_id: str) -> Optional[Device]:
        return Device.query.get(device_id)

    @staticmethod
    def find_all(status: str = None, device_type: str = None, agent_id: str = None) -> List[Device]:
        query = Device.query
        if status:
            query = query.filter_by(status=status)
        if device_type:
            query = query.filter_by(device_type=device_type)
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        return query.order_by(Device.last_seen.desc()).all()

    @staticmethod
    def create_or_update(ip_address: str, agent_id: str, data: dict) -> Device:
        device = Device.query.filter_by(ip_address=ip_address, agent_id=agent_id).first()
        now = datetime.now(timezone.utc)

        if device:
            for key in ["mac_address", "hostname", "vendor", "device_type",
                         "os_detection", "os_confidence", "classification_confidence"]:
                if key in data and data[key] is not None:
                    setattr(device, key, data[key])
            device.status = data.get("status", "online")
            device.last_seen = now
        else:
            device = Device(
                ip_address=ip_address,
                agent_id=agent_id,
                mac_address=data.get("mac_address"),
                hostname=data.get("hostname"),
                vendor=data.get("vendor"),
                device_type=data.get("device_type"),
                os_detection=data.get("os_detection"),
                os_confidence=data.get("os_confidence"),
                classification_confidence=data.get("classification_confidence"),
                status=data.get("status", "online"),
                first_seen=now,
                last_seen=now,
            )
            db.session.add(device)

        db.session.commit()
        return device

    @staticmethod
    def update_status(device_id: str, status: str) -> Device:
        device = Device.query.get(device_id)
        if device:
            device.status = status
            device.last_seen = datetime.now(timezone.utc)
            db.session.commit()
        return device

    @staticmethod
    def count_by_status() -> dict:
        results = db.session.query(
            Device.status, db.func.count(Device.id)
        ).group_by(Device.status).all()
        return {status: count for status, count in results}


class ServiceRepository:

    @staticmethod
    def find_by_device(device_id: str) -> List[Service]:
        return Service.query.filter_by(device_id=device_id).all()

    @staticmethod
    def upsert(device_id: str, port: int, protocol: str, data: dict) -> Service:
        service = Service.query.filter_by(
            device_id=device_id, port=port, protocol=protocol
        ).first()
        now = datetime.now(timezone.utc)

        if service:
            for key in ["service_name", "version", "banner", "state", "confidence"]:
                if key in data and data[key] is not None:
                    setattr(service, key, data[key])
            service.last_seen = now
        else:
            service = Service(
                device_id=device_id,
                port=port,
                protocol=protocol,
                service_name=data.get("service_name"),
                version=data.get("version"),
                banner=data.get("banner"),
                state=data.get("state", "open"),
                confidence=data.get("confidence"),
                first_seen=now,
                last_seen=now,
            )
            db.session.add(service)

        db.session.commit()
        return service


class InterfaceRepository:

    @staticmethod
    def find_by_device(device_id: str) -> List[NetworkInterface]:
        return NetworkInterface.query.filter_by(device_id=device_id).all()

    @staticmethod
    def upsert(device_id: str, name: str, data: dict) -> NetworkInterface:
        iface = NetworkInterface.query.filter_by(
            device_id=device_id, name=name
        ).first()
        now = datetime.now(timezone.utc)

        if iface:
            for key in ["mac_address", "ip_address", "subnet_mask", "interface_type",
                         "speed", "is_up", "mtu"]:
                if key in data and data[key] is not None:
                    setattr(iface, key, data[key])
            iface.last_seen = now
        else:
            iface = NetworkInterface(
                device_id=device_id,
                name=name,
                mac_address=data.get("mac_address"),
                ip_address=data.get("ip_address"),
                subnet_mask=data.get("subnet_mask"),
                interface_type=data.get("interface_type"),
                speed=data.get("speed"),
                is_up=data.get("is_up", False),
                mtu=data.get("mtu"),
                first_seen=now,
                last_seen=now,
            )
            db.session.add(iface)

        db.session.commit()
        return iface

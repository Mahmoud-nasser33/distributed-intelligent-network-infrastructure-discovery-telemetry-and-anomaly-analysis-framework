from flask import Blueprint, jsonify, request, current_app
from app.repositories.scan_job_repo import ScanJobRepository
from app.utils.errors import NotFoundError, ValidationError
from app.services.discovery_service import DiscoveryOrchestrator
from app.config.settings import Config

discovery_bp = Blueprint("discovery", __name__)

_orchestrator = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        nmap_path = Config.NMAP_PATH
        _orchestrator = DiscoveryOrchestrator(nmap_path=nmap_path)
    return _orchestrator


@discovery_bp.route("/discovery/jobs", methods=["GET"])
def list_jobs():
    status = request.args.get("status")
    agent_id = request.args.get("agent_id")
    jobs = ScanJobRepository.find_all(status=status, agent_id=agent_id)
    return jsonify({
        "jobs": [j.to_dict() for j in jobs],
        "count": len(jobs),
    })


@discovery_bp.route("/discovery/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    job = ScanJobRepository.find_by_id(job_id)
    if not job:
        raise NotFoundError(f"Scan job {job_id} not found")
    return jsonify({"job": job.to_dict()})


@discovery_bp.route("/discovery/jobs", methods=["POST"])
def create_job():
    data = request.get_json()
    if not data or not data.get("target"):
        raise ValidationError("Target is required")

    job = ScanJobRepository.create({
        "agent_id": data.get("agent_id"),
        "target": data["target"],
        "scan_type": data.get("scan_type", "host"),
        "scan_arguments": data.get("scan_arguments"),
    })

    if data.get("run_async", True):
        task_id = current_app.task_manager.submit_discovery(
            scan_job_id=job.id,
            target=data["target"],
            agent_id=data.get("agent_id"),
            scan_type=data.get("scan_type", "host"),
            providers=data.get("providers"),
            arguments=data.get("scan_arguments"),
        )
        return jsonify({
            "job": job.to_dict(),
            "task_id": task_id,
            "message": "Discovery job queued",
        }), 202
    else:
        orch = _get_orchestrator()
        result = orch.run_discovery(
            scan_job_id=job.id,
            target=data["target"],
            agent_id=data.get("agent_id"),
            scan_type=data.get("scan_type", "host"),
            providers=data.get("providers"),
            arguments=data.get("scan_arguments"),
        )
        job = ScanJobRepository.find_by_id(job.id)
        return jsonify({
            "job": job.to_dict(),
            "result": result,
        })


@discovery_bp.route("/discovery/providers", methods=["GET"])
def list_providers():
    orch = _get_orchestrator()
    return jsonify({
        "providers": orch.get_provider_status(),
    })

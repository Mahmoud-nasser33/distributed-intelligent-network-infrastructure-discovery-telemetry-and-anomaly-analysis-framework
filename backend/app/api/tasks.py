from flask import Blueprint, jsonify, request, current_app
from app.utils.errors import NotFoundError

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/tasks", methods=["GET"])
def list_tasks():
    task_type = request.args.get("type")
    status = request.args.get("status")
    tasks = current_app.task_manager.list_tasks(
        task_type=task_type, status=status,
    )
    return jsonify({
        "tasks": tasks,
        "count": len(tasks),
    })


@tasks_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    task = current_app.task_manager.get_task(task_id)
    if not task:
        raise NotFoundError(f"Task {task_id} not found")
    return jsonify({"task": task})


@tasks_bp.route("/tasks/cleanup", methods=["POST"])
def cleanup_tasks():
    data = request.get_json() or {}
    max_age = data.get("max_age_seconds", 3600)
    removed = current_app.task_manager.cleanup_old_tasks(max_age)
    return jsonify({"removed": removed})


@tasks_bp.route("/tasks/scheduler", methods=["GET"])
def get_scheduler_status():
    jobs = current_app.task_scheduler.get_jobs()
    return jsonify({
        "scheduler_running": current_app.task_scheduler._started,
        "jobs": jobs,
    })

from flask import Flask, send_from_directory
from flask_cors import CORS
from pathlib import Path

from app.config.settings import Config, config_by_name
from app.config.database import db, migrate
from app.utils.logger import setup_logging
from app.api import api_bp
from app.utils.errors import register_error_handlers


def create_app(config_class=None):
    if config_class is None:
        config_class = Config
    elif isinstance(config_class, str):
        config_class = config_by_name.get(config_class, Config)

    app = Flask(__name__)
    app.config.from_object(config_class)

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        if not db_path.startswith(":"):
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    app.register_blueprint(api_bp, url_prefix="/api")
    register_error_handlers(app)

    from app.tasks.manager import TaskManager
    app.task_manager = TaskManager(app)

    from app.tasks.scheduler import TaskScheduler
    app.task_scheduler = TaskScheduler()
    app.task_scheduler.init_app(app)

    static_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "static"

    @app.route("/")
    @app.route("/<path:path>")
    def serve_static(path=""):
        if path and (static_dir / path).is_file():
            return send_from_directory(str(static_dir), path)
        return send_from_directory(str(static_dir), "index.html")

    @app.route("/health")
    def health():
        return {"status": "healthy", "service": "dinas"}

    with app.app_context():
        from app.models import device, observation, agent, telemetry, topology, anomaly, discovery
        db.create_all()

    app.task_scheduler.start()

    return app

import os
from app import create_app

config_name = os.environ.get("DINAS_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    app.run(
        host=os.environ.get("DINAS_HOST", "127.0.0.1"),
        port=int(os.environ.get("DINAS_PORT", "5000")),
        debug=False,
    )

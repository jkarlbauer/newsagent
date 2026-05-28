from config import config
from dashboard.app import app

if __name__ == "__main__":
    port = config.get("dashboard_port", 5050)
    app.run(host="0.0.0.0", port=port, debug=False)

from flask import Flask, jsonify, render_template

app = Flask(__name__)


@app.get("/")
def index():
    """Render the main HTML page with Speed Insights enabled"""
    return render_template("index.html")


@app.get("/api")
def api_info():
    """API information endpoint"""
    return jsonify(
        {
            "service": "neobank-notification-engine",
            "status": "ok",
            "message": "Notification engine API is running",
        }
    )


@app.get("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

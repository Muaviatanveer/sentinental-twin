from flask import Flask, jsonify
import requests
import psycopg2
import os

app = Flask(__name__)
API_URL = os.environ.get("API_URL", "http://api:8080")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Sentinel E-Commerce</title></head>
<body style="font-family: sans-serif; padding: 2rem;">
    <h1>Sentinel Merch Store</h1>
    <h3>Products (Loaded securely via API):</h3>
    <pre id="products" style="background: #f4f4f4; padding: 1rem;">Loading...</pre>
    
    <h3 style="color: red;">Security Flaw Check (Frontend -> Database direct):</h3>
    <button onclick="testDb()" style="padding: 10px; background: red; color: white; border: none; cursor: pointer;">
        Attempt Direct DB Connection
    </button>
    <pre id="db-result" style="background: #fee; padding: 1rem; margin-top: 10px;"></pre>

    <script>
        fetch('/api-proxy').then(r => r.json()).then(data => {
            document.getElementById('products').innerText = JSON.stringify(data, null, 2);
        });
        function testDb() {
            document.getElementById('db-result').innerText = 'Connecting...';
            fetch('/test-db').then(r => r.json()).then(data => {
                document.getElementById('db-result').innerText = JSON.stringify(data, null, 2);
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_TEMPLATE

@app.route("/api-proxy")
def api_proxy():
    try:
        resp = requests.get(f"{API_URL}/products", timeout=2)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test-db")
def test_db():
    # INTENTIONAL FLAW: Frontend trying to reach DB directly bypassing API
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "database"),
            database=os.environ.get("DB_NAME", "commerce"),
            user=os.environ.get("DB_USER", "admin"),
            password=os.environ.get("DB_PASS", "password"),
            connect_timeout=2
        )
        conn.close()
        return jsonify({"status": "DANGER", "message": "Frontend successfully connected directly to Database! (Network is too flat)"})
    except Exception as e:
        return jsonify({"status": "SECURE", "message": "Direct DB connection blocked.", "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

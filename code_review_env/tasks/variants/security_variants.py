"""Security audit variants — 2 different web applications."""

VARIANT_1 = {
    "filename": "app.py",
    "code": '''
import os
import sqlite3
import pickle
import subprocess
import hashlib
import hmac
from flask import Flask, request, send_file, redirect, jsonify, abort

app = Flask(__name__)
DB_PATH = "app.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")


def get_db():
    return sqlite3.connect(DB_PATH)


def verify_webhook(payload: bytes, signature: str) -> bool:
    """Verify webhook signature using HMAC-SHA256."""
    expected = hmac.new(
        SECRET_KEY.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    hashed = hashlib.md5(password.encode()).hexdigest()
    db = get_db()
    query = f"SELECT * FROM users WHERE username=\\'{username}\\' AND password_hash=\\'{hashed}\\'"
    user = db.execute(query).fetchone()
    if user:
        return {"status": "ok", "user_id": user[0]}
    return {"status": "error"}, 401


@app.route("/profile/<user_id>")
def profile(user_id):
    db = get_db()
    user = db.execute(f"SELECT * FROM users WHERE id={user_id}").fetchone()
    return {"username": user[1], "email": user[2]}


@app.route("/export", methods=["POST"])
def export_data():
    data = request.get_data()
    obj = pickle.loads(data)
    return {"result": str(obj)}


@app.route("/download")
def download():
    filename = request.args.get("file")
    filepath = os.path.join("/app/uploads", filename)
    return send_file(filepath)


@app.route("/run-report")
def run_report():
    report_name = request.args.get("name")
    result = subprocess.run(
        f"python reports/{report_name}.py",
        shell=True, capture_output=True, text=True
    )
    return {"output": result.stdout}


@app.route("/redirect")
def open_redirect():
    url = request.args.get("url")
    return redirect(url)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    return f"<h1>Results for: {q}</h1>"


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig = request.headers.get("X-Signature", "")
    if not verify_webhook(payload, sig):
        abort(403)
    return jsonify({"status": "received"})


@app.route("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}
''',
    "issues": [
        {"line": 30, "issue": "weak_hashing", "severity": "medium",
         "description": "Using MD5 for password hashing. MD5 is cryptographically broken. Use bcrypt or argon2."},
        {"line": 32, "issue": "sql_injection", "severity": "critical",
         "description": "SQL injection via f-string query with unsanitized username. Use parameterized queries."},
        {"line": 39, "issue": "sql_injection", "severity": "critical",
         "description": "SQL injection in profile endpoint. user_id interpolated directly into query."},
        {"line": 45, "issue": "insecure_deserialization", "severity": "critical",
         "description": "pickle.loads on untrusted user data allows arbitrary code execution."},
        {"line": 51, "issue": "path_traversal", "severity": "critical",
         "description": "Path traversal in download. Attacker can use ../ to read arbitrary files."},
        {"line": 57, "issue": "command_injection", "severity": "critical",
         "description": "Command injection via shell=True with user-controlled report_name."},
        {"line": 65, "issue": "open_redirect", "severity": "medium",
         "description": "Open redirect. User-controlled URL passed directly to redirect()."},
        {"line": 70, "issue": "xss", "severity": "high",
         "description": "Reflected XSS. User input q rendered directly in HTML without escaping."},
    ],
}

VARIANT_2 = {
    "filename": "file_service.py",
    "code": '''
import os
import yaml
import shutil
import hashlib
import secrets
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_DIR = "/app/uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "doc", "docx"}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file"}), 400
    filename = file.filename
    dest = os.path.join(UPLOAD_DIR, filename)
    file.save(dest)
    return jsonify({"path": dest, "size": os.path.getsize(dest)})


@app.route("/config", methods=["POST"])
def load_config():
    raw = request.get_data()
    config = yaml.load(raw)
    return jsonify({"keys": list(config.keys())})


@app.route("/files/<path:filepath>")
def serve_file(filepath):
    return send_from_directory("/", filepath)


@app.route("/template")
def render_template_str():
    name = request.args.get("name", "World")
    template = request.args.get("template", "Hello, {name}!")
    return template.format(name=name)


@app.route("/exec", methods=["POST"])
def execute():
    code = request.json.get("code", "")
    result = eval(code)
    return jsonify({"result": str(result)})


@app.route("/compare")
def compare_hash():
    user_hash = request.args.get("hash", "")
    expected = hashlib.sha256(b"admin_secret").hexdigest()
    if user_hash == expected:
        return jsonify({"access": True})
    return jsonify({"access": False})


@app.route("/cleanup", methods=["POST"])
def cleanup():
    path = request.json.get("path", "")
    if os.path.exists(path):
        shutil.rmtree(path)
        return jsonify({"deleted": path})
    return jsonify({"error": "not found"}), 404


@app.route("/share/<token>")
def get_shared(token):
    """Retrieve a shared file by token."""
    filepath = os.path.join(UPLOAD_DIR, f"shared_{token}")
    if os.path.exists(filepath):
        return send_from_directory(UPLOAD_DIR, f"shared_{token}")
    return jsonify({"error": "not found"}), 404
''',
    "issues": [
        {"line": 29, "issue": "unsanitized_filename", "severity": "critical",
         "description": "upload() uses file.filename directly without secure_filename(). Attacker can upload with path traversal filename like '../../etc/cron.d/malicious' to write anywhere on disk."},
        {"line": 30, "issue": "path_disclosure", "severity": "medium",
         "description": "upload() returns the full server file path in response. Leaks internal directory structure to attacker."},
        {"line": 37, "issue": "yaml_deserialization", "severity": "critical",
         "description": "yaml.load() without Loader parameter allows arbitrary Python object construction. Use yaml.safe_load() instead."},
        {"line": 42, "issue": "directory_traversal_serve", "severity": "critical",
         "description": "serve_file() uses send_from_directory with root '/'. Attacker can access any file on the system via /files/etc/passwd."},
        {"line": 48, "issue": "server_side_template_injection", "severity": "critical",
         "description": "render_template_str() uses str.format() with user-controlled template string. Attacker can inject {name.__class__.__mro__} to leak internal objects. Use proper template engine with sandboxing."},
        {"line": 54, "issue": "arbitrary_code_execution", "severity": "critical",
         "description": "execute() calls eval() on user-supplied code. Allows complete system compromise. Never use eval on untrusted input."},
        {"line": 60, "issue": "timing_attack", "severity": "medium",
         "description": "compare_hash() uses == for hash comparison. Vulnerable to timing attack. Use hmac.compare_digest() for constant-time comparison."},
        {"line": 67, "issue": "arbitrary_file_deletion", "severity": "critical",
         "description": "cleanup() deletes any path the user specifies with shutil.rmtree(). Attacker can delete /app, /etc, or entire filesystem. Must restrict to allowed directories."},
    ],
}

VARIANTS = [VARIANT_1, VARIANT_2]

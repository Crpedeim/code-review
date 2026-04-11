"""Diff review variants — 2 different pull request diffs."""

VARIANT_1 = {
    "filename": "auth/session_manager.py (diff)",
    "code": '''
--- a/auth/session_manager.py
+++ b/auth/session_manager.py
@@ -1,6 +1,8 @@
 import time
 import hashlib
 import secrets
+import json
+import os
 from typing import Optional, Dict

 class SessionManager:
@@ -12,15 +14,20 @@
         self.sessions: Dict[str, dict] = {}
         self.secret_key = secret_key

-    def create_session(self, user_id: int) -> str:
-        """Create a new session and return the session token."""
-        token = secrets.token_urlsafe(32)
+    def create_session(self, user_id: int, remember_me: bool = False) -> str:
+        """Create session. If remember_me, session lasts 30 days."""
+        token = hashlib.md5(str(user_id).encode()).hexdigest()
         expiry = time.time() + self.default_ttl
+        if remember_me:
+            expiry = time.time() + (30 * 24 * 3600)
         self.sessions[token] = {
             "user_id": user_id,
             "created_at": time.time(),
             "expires_at": expiry,
+            "remember_me": remember_me,
         }
+        log_path = f"/tmp/sessions/{user_id}.log"
+        open(log_path, "a").write(f"Session created: {token}\\n")
         return token

     def validate_session(self, token: str) -> Optional[int]:
@@ -35,10 +42,18 @@
             return None
         return session["user_id"]

-    def revoke_session(self, token: str) -> bool:
-        """Revoke a session."""
-        if token in self.sessions:
-            del self.sessions[token]
+    def revoke_session(self, token: str = None, user_id: int = None) -> bool:
+        """Revoke session by token, or all sessions for a user_id."""
+        if token and token in self.sessions:
+            self.sessions[token]["expires_at"] = 0
             return True
+        if user_id:
+            for t, s in self.sessions.items():
+                if s["user_id"] == user_id:
+                    s["expires_at"] = 0
+            return True
         return False

+    def export_sessions(self, filepath: str):
+        """Export all active sessions to a JSON file."""
+        with open(filepath, "w") as f:
+            json.dump(self.sessions, f)
''',
    "issues": [
        {"line": 20, "issue": "predictable_session_token", "severity": "critical",
         "description": "Changed from secrets.token_urlsafe(32) to hashlib.md5(user_id). Tokens are now predictable. Session hijacking vulnerability."},
        {"line": 30, "issue": "resource_leak_file_handle", "severity": "medium",
         "description": "open() without context manager leaks file handles."},
        {"line": 30, "issue": "path_injection_log", "severity": "high",
         "description": "Log path uses user_id in f-string. Path traversal if user_id is attacker-controlled."},
        {"line": 30, "issue": "sensitive_data_in_log", "severity": "high",
         "description": "Session token written to log in plaintext. Token theft if logs are accessible."},
        {"line": 47, "issue": "revoke_does_not_delete", "severity": "high",
         "description": "revoke sets expires_at=0 instead of deleting. Session data stays in memory forever."},
        {"line": 58, "issue": "export_leaks_sessions", "severity": "critical",
         "description": "export_sessions dumps all tokens to file in plaintext. Mass session compromise."},
        {"line": 4, "issue": "unused_import_os", "severity": "low",
         "description": "os module imported but never used."},
    ],
}

VARIANT_2 = {
    "filename": "db/migration_helper.py (diff)",
    "code": '''
--- a/db/migration_helper.py
+++ b/db/migration_helper.py
@@ -1,5 +1,6 @@
 import sqlite3
 import logging
+import subprocess
 from pathlib import Path
 from typing import List, Optional

@@ -15,14 +16,21 @@
     def __init__(self, db_path: str, migrations_dir: str = "migrations"):
         self.db_path = db_path
         self.migrations_dir = Path(migrations_dir)
-        self.conn = sqlite3.connect(db_path)
+        self.conn = sqlite3.connect(db_path, check_same_thread=False)
         self._ensure_migration_table()

     def _ensure_migration_table(self):
         self.conn.execute("""
             CREATE TABLE IF NOT EXISTS schema_migrations (
                 version TEXT PRIMARY KEY,
-                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+                applied_by TEXT DEFAULT 'system'
             )
         """)
         self.conn.commit()
@@ -35,16 +43,30 @@
         """Get list of already-applied migration versions."""
         rows = self.conn.execute(
             "SELECT version FROM schema_migrations ORDER BY version"
         ).fetchall()
         return [row[0] for row in rows]

-    def apply_migration(self, version: str, sql: str) -> bool:
-        """Apply a single migration."""
+    def apply_migration(self, version: str, sql: str = None,
+                        script: str = None) -> bool:
+        """Apply a migration from SQL string or external script."""
         try:
-            self.conn.executescript(sql)
-            self.conn.execute(
-                "INSERT INTO schema_migrations (version) VALUES (?)",
-                (version,)
-            )
-            self.conn.commit()
+            if script:
+                result = subprocess.run(
+                    f"python {script}",
+                    shell=True, capture_output=True, text=True
+                )
+                if result.returncode != 0:
+                    logger.error(f"Script failed: {result.stderr}")
+                    return False
+            elif sql:
+                self.conn.executescript(sql)
+            self.conn.execute(
+                f"INSERT INTO schema_migrations (version, applied_by) "
+                f"VALUES ('{version}', '{self._get_user()}')"
+            )
+            self.conn.commit()
             logger.info(f"Applied migration {version}")
             return True
         except Exception as e:
-            self.conn.rollback()
             logger.error(f"Migration {version} failed: {e}")
             return False

+    def _get_user(self) -> str:
+        """Get current system user for audit trail."""
+        import getpass
+        return getpass.getuser()
+
     def run_pending(self) -> int:
         """Apply all pending migrations in order."""
         applied = set(self.get_applied_versions())
@@ -60,5 +82,12 @@
             count += 1
         return count

+    def rollback(self, version: str):
+        """Remove a migration record."""
+        self.conn.execute(
+            f"DELETE FROM schema_migrations WHERE version = '{version}'"
+        )
+        self.conn.commit()
+
     def close(self):
         self.conn.close()
''',
    "issues": [
        {"line": 55, "issue": "command_injection_script", "severity": "critical",
         "description": "apply_migration() runs external script with shell=True using f-string. If script path is user-controlled, this is command injection. Use subprocess.run with a list, not shell=True."},
        {"line": 63, "issue": "sql_injection_version", "severity": "critical",
         "description": "INSERT uses f-string with version and _get_user(). Both could contain SQL injection payloads. Use parameterized queries with ? placeholders. This is a regression from the old parameterized code."},
        {"line": 70, "issue": "removed_rollback_on_error", "severity": "high",
         "description": "The except block no longer calls self.conn.rollback(). Failed migrations leave the database in a partially-applied state. The old code correctly rolled back."},
        {"line": 19, "issue": "check_same_thread_false", "severity": "medium",
         "description": "check_same_thread=False allows SQLite connection sharing across threads. SQLite is not thread-safe for writes. This can cause database corruption under concurrent access."},
        {"line": 87, "issue": "sql_injection_rollback", "severity": "critical",
         "description": "rollback() uses f-string for DELETE query. SQL injection via version parameter. Use parameterized query."},
        {"line": 87, "issue": "rollback_no_undo", "severity": "high",
         "description": "rollback() only deletes the migration record but does not reverse the schema changes. The database schema and migration table become inconsistent."},
    ],
}

VARIANTS = [VARIANT_1, VARIANT_2]

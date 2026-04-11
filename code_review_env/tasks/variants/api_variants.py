"""API design review variants — 2 different service layers."""

VARIANT_1 = {
    "filename": "user_service.py",
    "code": '''
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)


class UserService:
    """Service layer for user management."""

    def __init__(self, db):
        self.db = db
        self._cache = {}

    def get_user(self, user_id: int) -> Optional[User]:
        if user_id in self._cache:
            return self._cache[user_id]
        row = self.db.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if row:
            user = User(*row)
            self._cache[user_id] = user
            return user
        return None

    def list_users(self, page: int = 1, limit: int = 100) -> List[User]:
        offset = (page - 1) * limit
        rows = self.db.execute(
            "SELECT id, name, email, created_at FROM users LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        return [User(*row) for row in rows]

    def create_user(self, name: str, email: str) -> User:
        cursor = self.db.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email)
        )
        return User(id=cursor.lastrowid, name=name, email=email)

    def delete_user(self, user_id: int) -> bool:
        self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return True

    def update_user(self, user_id: int, name: str = None, email: str = None) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None
        if name:
            user.name = name
        if email:
            user.email = email
        self.db.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            (user.name, user.email, user_id)
        )
        return user

    def search_users(self, query: str) -> List[User]:
        rows = self.db.execute(
            f"SELECT id, name, email, created_at FROM users WHERE name LIKE '%{query}%'"
        ).fetchall()
        return [User(*row) for row in rows]

    def get_user_activity(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        user = self.get_user(user_id)
        if not user:
            return {"error": "User not found"}
        cutoff = datetime.now() - timedelta(days=days)
        rows = self.db.execute(
            "SELECT action, COUNT(*) FROM activity_log "
            "WHERE user_id = ? AND timestamp > ? GROUP BY action",
            (user_id, cutoff)
        ).fetchall()
        return {
            "user_id": user_id,
            "period_days": days,
            "actions": {row[0]: row[1] for row in rows},
            "total": sum(row[1] for row in rows),
        }

    def bulk_delete(self, user_ids: List[int]) -> int:
        deleted = 0
        for uid in user_ids:
            self.db.execute("DELETE FROM users WHERE id = ?", (uid,))
            deleted += 1
        return deleted

    def export_users(self, format: str = "json") -> str:
        rows = self.db.execute("SELECT * FROM users").fetchall()
        if format == "json":
            return json.dumps([{"id": r[0], "name": r[1], "email": r[2]} for r in rows])
        elif format == "csv":
            lines = ["id,name,email"]
            lines.extend(f"{r[0]},{r[1]},{r[2]}" for r in rows)
            return "\\n".join(lines)
        return ""
''',
    "issues": [
        {"line": 56, "issue": "cache_not_invalidated_on_delete", "severity": "high",
         "description": "delete_user() removes from DB but not from self._cache. get_user() returns ghost user."},
        {"line": 65, "issue": "cache_stale_on_update", "severity": "high",
         "description": "update_user() modifies cached object but inconsistently. Cache miss path creates uncached user."},
        {"line": 75, "issue": "sql_injection_in_search", "severity": "critical",
         "description": "search_users() uses f-string for LIKE query. SQL injection. Use parameterized query."},
        {"line": 57, "issue": "delete_always_returns_true", "severity": "medium",
         "description": "delete_user() always returns True even if user does not exist. Check rowcount."},
        {"line": 98, "issue": "bulk_delete_no_transaction", "severity": "medium",
         "description": "bulk_delete() has no transaction. Partial failure leaves inconsistent state."},
        {"line": 106, "issue": "csv_injection", "severity": "medium",
         "description": "export_users() CSV mode does not escape commas or quotes. CSV formula injection possible."},
        {"line": 37, "issue": "unbounded_cache", "severity": "medium",
         "description": "get_user() caches without eviction. Memory grows unbounded."},
        {"line": 17, "issue": "mutable_default_datetime", "severity": "low",
         "description": "User.created_at default_factory=datetime.now captures instantiation time, not DB creation time."},
    ],
}

VARIANT_2 = {
    "filename": "payment_service.py",
    "code": '''
import time
import json
import logging
import hashlib
from typing import Optional, List, Dict
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Payment:
    id: int
    user_id: int
    amount: float
    currency: str
    status: PaymentStatus
    created_at: float


class PaymentService:
    """Service layer for payment processing."""

    def __init__(self, db, gateway):
        self.db = db
        self.gateway = gateway
        self._idempotency_keys = {}

    def create_payment(self, user_id: int, amount: float, currency: str,
                       idempotency_key: str = None) -> Payment:
        """Create a new payment."""
        if idempotency_key and idempotency_key in self._idempotency_keys:
            return self._idempotency_keys[idempotency_key]

        cursor = self.db.execute(
            "INSERT INTO payments (user_id, amount, currency, status) VALUES (?, ?, ?, ?)",
            (user_id, amount, currency, "pending")
        )
        payment = Payment(
            id=cursor.lastrowid, user_id=user_id, amount=amount,
            currency=currency, status=PaymentStatus.PENDING,
            created_at=time.time()
        )
        if idempotency_key:
            self._idempotency_keys[idempotency_key] = payment
        return payment

    def process_payment(self, payment_id: int) -> bool:
        """Charge the payment through the gateway."""
        row = self.db.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()
        if not row:
            return False

        result = self.gateway.charge(row[2], row[3])
        if result["success"]:
            self.db.execute(
                "UPDATE payments SET status = ? WHERE id = ?",
                ("completed", payment_id)
            )
        return result["success"]

    def refund(self, payment_id: int, reason: str = "") -> bool:
        """Refund a completed payment."""
        row = self.db.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()
        if not row:
            return False

        self.gateway.refund(row[2], row[3])
        self.db.execute(
            "UPDATE payments SET status = ? WHERE id = ?",
            ("refunded", payment_id)
        )
        return True

    def get_user_total(self, user_id: int) -> float:
        """Get total amount spent by a user."""
        rows = self.db.execute(
            "SELECT amount FROM payments WHERE user_id = ? AND status = 'completed'",
            (user_id,)
        ).fetchall()
        return sum(row[0] for row in rows)

    def generate_receipt(self, payment_id: int) -> str:
        """Generate a receipt hash for verification."""
        row = self.db.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()
        receipt_data = f"{row[0]}:{row[1]}:{row[2]}:{row[3]}"
        return hashlib.md5(receipt_data.encode()).hexdigest()

    def get_payments_by_status(self, status: str) -> List[Dict]:
        """Get all payments with given status."""
        rows = self.db.execute(
            f"SELECT * FROM payments WHERE status = '{status}'"
        ).fetchall()
        return [{"id": r[0], "amount": r[2], "status": r[4]} for r in rows]

    def export_for_audit(self, filepath: str):
        """Export all payment data for auditing."""
        rows = self.db.execute("SELECT * FROM payments").fetchall()
        with open(filepath, "w") as f:
            json.dump([list(r) for r in rows], f)
        logger.info(f"Exported {len(rows)} payments to {filepath}")
''',
    "issues": [
        {"line": 25, "issue": "float_for_money", "severity": "high",
         "description": "Payment.amount uses float for monetary values. Floating point causes rounding errors (0.1 + 0.2 != 0.3). Use Decimal for financial calculations."},
        {"line": 73, "issue": "refund_no_status_check", "severity": "high",
         "description": "refund() does not check if payment status is 'completed'. Can refund pending, failed, or already-refunded payments. Must verify status before refunding."},
        {"line": 75, "issue": "refund_no_error_handling", "severity": "high",
         "description": "refund() calls gateway.refund() but does not check if it succeeded. Marks payment as refunded in DB even if the gateway refund failed."},
        {"line": 93, "issue": "weak_receipt_hash", "severity": "medium",
         "description": "generate_receipt() uses MD5 which is broken. Receipt hashes can be forged. Use SHA-256 or HMAC."},
        {"line": 99, "issue": "sql_injection_status", "severity": "critical",
         "description": "get_payments_by_status() uses f-string for SQL. SQL injection via status parameter. Use parameterized query."},
        {"line": 40, "issue": "idempotency_not_persisted", "severity": "medium",
         "description": "Idempotency keys stored in memory dict. Lost on restart. Should be persisted to database."},
        {"line": 40, "issue": "idempotency_unbounded", "severity": "medium",
         "description": "Idempotency keys dict grows unbounded. No TTL or eviction. Memory leak over time."},
        {"line": 63, "issue": "no_status_check_before_charge", "severity": "high",
         "description": "process_payment() does not verify payment is still pending. A completed payment could be charged again (double charge)."},
    ],
}

VARIANTS = [VARIANT_1, VARIANT_2]

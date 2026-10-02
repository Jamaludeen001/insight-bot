# db.py
import json
import logging
import secrets
from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from config import DATABASE_URL
from utils.exceptions import DatabaseError

logger = logging.getLogger("insight_bot")

SHORT_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
SHORT_ID_LEN = 6
MAX_ID_RETRIES = 5


def _generate_short_id(prefix: str) -> str:
    body = "".join(secrets.choice(SHORT_ID_ALPHABET) for _ in range(SHORT_ID_LEN))
    return f"{prefix}-{body}"


def _is_uuid(value: str) -> bool:
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


def _connect():
    try:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        raise DatabaseError(f"Could not connect to database: {e}") from e


# ── Products ─────────────────────────────────────────
def get_product_by_order_id(order_id: str) -> Optional[dict]:
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE order_id = %s", (order_id,))
            return cur.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e


# ── Damage reports ──────────────────────────────────
def insert_damage_report(
    *,
    order_id: str,
    feedback: str,
    sentiment: str,
    sentiment_score: float,
    damage_severity: float,
    damage_details: dict,
    damaged_image_path: Optional[str] = None,
    status: str = "open",
) -> str:
    last_err = None
    for attempt in range(MAX_ID_RETRIES):
        short_id = _generate_short_id("RPT")
        try:
            with _connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO damage_reports
                      (order_id, feedback, sentiment, sentiment_score,
                       damage_severity, damage_details, status, short_id,
                       damaged_image_path)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING short_id
                    """,
                    (
                        order_id, feedback, sentiment, sentiment_score,
                        damage_severity, json.dumps(damage_details),
                        status, short_id, damaged_image_path,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return str(row["short_id"])
        except Exception as e:
            last_err = e
            if "uniq_reports_short_id" in str(e) or (
                "duplicate key" in str(e).lower() and "short_id" in str(e).lower()
            ):
                logger.warning(f"short_id collision attempt {attempt + 1}: {short_id}")
                continue
            raise DatabaseError(str(e)) from e

    raise DatabaseError(
        f"Could not generate a unique report ID after {MAX_ID_RETRIES} attempts: {last_err}"
    )


def get_report_by_short_id(short_id: str) -> Optional[dict]:
    if not short_id:
        return None
    short_id = short_id.strip().upper()
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM damage_reports WHERE short_id = %s", (short_id,))
            return cur.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e


def get_report_by_tracking_id(tracking_id: str) -> Optional[dict]:
    if not _is_uuid(tracking_id):
        return None
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM damage_reports WHERE tracking_id = %s", (tracking_id,))
            return cur.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e


# ── Warranty claims ──────────────────────────────────
def insert_warranty_claim(
    *,
    order_id: str,
    claim_type: str,
    reason: str,
    image_path: str,
    damage_severity: float,
    policy_snapshot: dict,
    damaged_image_path: Optional[str] = None,
    status: str = "submitted",
) -> str:
    last_err = None
    for attempt in range(MAX_ID_RETRIES):
        short_id = _generate_short_id("CLM")
        try:
            with _connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO warranty_claims
                      (order_id, claim_type, reason, image_path,
                       damage_severity, policy_snapshot, status, short_id,
                       damaged_image_path)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING short_id
                    """,
                    (
                        order_id, claim_type, reason, image_path,
                        damage_severity, json.dumps(policy_snapshot),
                        status, short_id,
                        damaged_image_path or image_path,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return str(row["short_id"])
        except Exception as e:
            last_err = e
            if "uniq_claims_short_id" in str(e) or (
                "duplicate key" in str(e).lower() and "short_id" in str(e).lower()
            ):
                logger.warning(f"short_id collision attempt {attempt + 1}: {short_id}")
                continue
            raise DatabaseError(str(e)) from e

    raise DatabaseError(
        f"Could not generate a unique claim ID after {MAX_ID_RETRIES} attempts: {last_err}"
    )


def get_warranty_claim_by_short_id(short_id: str) -> Optional[dict]:
    if not short_id:
        return None
    short_id = short_id.strip().upper()
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM warranty_claims WHERE short_id = %s", (short_id,))
            return cur.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e


def get_warranty_claim_by_id(claim_id: str) -> Optional[dict]:
    if not _is_uuid(claim_id):
        return None
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM warranty_claims WHERE claim_id = %s", (claim_id,))
            return cur.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e


def get_active_claim_for_order(order_id: str) -> Optional[dict]:
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM warranty_claims
                WHERE order_id = %s AND status <> 'rejected'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (order_id,),
            )
            return cur.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e

def get_open_report_for_order(order_id: str) -> Optional[dict]:
    """Return the current open report for this order, if any."""
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM damage_reports
                WHERE order_id = %s AND status = 'open'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (order_id,),
            )
            return cur.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e


def update_damage_report(
    *,
    tracking_id: str,
    feedback: str,
    sentiment: str,
    sentiment_score: float,
    damage_severity: float,
    damage_details: dict,
    damaged_image_path: Optional[str] = None,
) -> str:
    """Update an existing open report in place. Returns its short_id."""
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE damage_reports
                   SET feedback          = %s,
                       sentiment         = %s,
                       sentiment_score   = %s,
                       damage_severity   = %s,
                       damage_details    = %s,
                       damaged_image_path = %s,
                       updated_at        = CURRENT_TIMESTAMP
                 WHERE tracking_id = %s
                 RETURNING short_id
                """,
                (
                    feedback, sentiment, sentiment_score,
                    damage_severity, json.dumps(damage_details),
                    damaged_image_path, tracking_id,
                ),
            )
            row = cur.fetchone()
            conn.commit()
            if not row:
                raise DatabaseError(f"Report {tracking_id} not found for update.")
            return str(row["short_id"])
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) from e
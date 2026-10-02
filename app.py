# app.py
import re
import uuid
from pathlib import Path
from datetime import date, timedelta
from uuid import UUID

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from utils.logger import setup_logger
from utils.exceptions import (
    ImageProcessingError,
    FeedbackProcessingError,
    DatabaseError,
)

from models.feedback_processor import FeedbackProcessor
from models.damage_analyzer import DamageAnalyzer
from models.report_generator import ReportGenerator
from models.warranty_claim_processor import WarrantyClaimProcessor

from config import NEGATIVE_THRESHOLD
from db import (
    get_product_by_order_id,
    insert_damage_report,
    update_damage_report,           
    get_open_report_for_order,     
    get_report_by_short_id,
    get_warranty_claim_by_short_id,
)


# ── App setup ─────────────────────────────────────────
app = FastAPI(title="Insight Bot API", version="1.0.0")
logger = setup_logger()

UPLOAD_DIR    = Path("uploads")
TEMPLATES_DIR = Path("templates")
STATIC_DIR    = Path("static")
DAMAGED_DIR   = Path("damaged_images")

for d in (UPLOAD_DIR, TEMPLATES_DIR, STATIC_DIR, DAMAGED_DIR):
    d.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images/damaged", StaticFiles(directory="damaged_images"), name="damaged")


# ── Constants ─────────────────────────────────────────
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
CHUNK_SIZE = 64 * 1024

_ID_CHARS = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
REPORT_ID_RE = re.compile(rf"^RPT-[{_ID_CHARS}]{{6}}$", re.IGNORECASE)
CLAIM_ID_RE  = re.compile(rf"^CLM-[{_ID_CHARS}]{{6}}$", re.IGNORECASE)


# ── Helpers ───────────────────────────────────────────
def save_upload(file: UploadFile, dest_dir: Path = UPLOAD_DIR) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    dest_dir.mkdir(exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = dest_dir / name
    written = 0
    try:
        with path.open("wb") as f:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024*1024)} MB.",
                    )
                f.write(chunk)
    except HTTPException:
        path.unlink(missing_ok=True)
        raise
    except Exception as e:
        path.unlink(missing_ok=True)
        logger.error(f"Failed writing upload: {e}")
        raise HTTPException(status_code=500, detail="Could not process the uploaded file.")

    return str(path)


def db_fail(endpoint: str, err: Exception) -> None:
    logger.error(f"[{endpoint}] DB error: {err}")
    raise HTTPException(status_code=500, detail="Something went wrong. Please try again later.")


def image_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"/images/damaged/{Path(path).name}"


# ── Global exception handler ─────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# ═══════════════════════════════════════════════════════
#  PAGE
# ═══════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def home():
    index = TEMPLATES_DIR / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>Insight Bot API is running</h1>"
                            "<p>Place templates/index.html to serve the UI.</p>")
    return HTMLResponse(index.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════
#  API: Validate Order + CRT
# ═══════════════════════════════════════════════════════
@app.get("/api/products/{order_id}")
async def validate_order(order_id: str):
    order_id = order_id.strip()
    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID is required.")

    try:
        product = get_product_by_order_id(order_id)
    except DatabaseError as e:
        db_fail("validate_order", e)

    if not product:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

    if not product.get("is_crt"):
        raise HTTPException(
            status_code=400,
            detail=f"Product '{product['product_name']}' is not eligible (not CRT).",
        )

    return {
        "order_id": product["order_id"],
        "product_name": product["product_name"],
        "is_crt": product["is_crt"],
        "warranty_status": product.get("warranty_status"),
    }


# ═══════════════════════════════════════════════════════
#  API: Raise Report
# ═══════════════════════════════════════════════════════
@app.post("/api/damage-report")
async def create_damage_report(
    order_id: str = Form(...),
    feedback: str = Form(...),
    image: UploadFile = File(...),
):
    order_id = order_id.strip()
    feedback = feedback.strip()

    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID is required.")
    if not feedback:
        raise HTTPException(status_code=400, detail="Feedback cannot be empty.")

    # 1. Validate order
    try:
        product = get_product_by_order_id(order_id)
    except DatabaseError as e:
        db_fail("create_damage_report:product", e)

    if not product:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
    if not product.get("is_crt"):
        raise HTTPException(
            status_code=400,
            detail=f"Product '{product['product_name']}' is not eligible (not CRT).",
        )

    # 2. ⭐ Look up existing OPEN report
    try:
        existing = get_open_report_for_order(order_id)
    except DatabaseError as e:
        db_fail("create_damage_report:existing", e)

    # 3. Sentiment
    try:
        sentiment, score = FeedbackProcessor().analyze_sentiment(feedback)
    except FeedbackProcessingError as e:
        logger.error(f"[create_damage_report] sentiment error: {e}")
        raise HTTPException(status_code=500, detail="Could not analyze feedback.")

    if not (sentiment == "negative" and score < NEGATIVE_THRESHOLD):
        return {
            "proceed": False,
            "sentiment": sentiment,
            "score": score,
            "message": "Feedback is not negative enough to raise a damage report.",
        }

    # 4. Save + analyze image
    try:
        damaged_path = save_upload(image, DAMAGED_DIR)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[create_damage_report] save error: {e}")
        raise HTTPException(status_code=500, detail="Could not save the uploaded image.")

    try:
        damage_report = DamageAnalyzer().analyze_damage(damaged_path)
    except ImageProcessingError as e:
        logger.error(f"[create_damage_report] image error: {e}")
        raise HTTPException(status_code=400, detail="Could not process the image.")

    if "error" in damage_report:
        raise HTTPException(status_code=400, detail=damage_report["error"])

    severity = float(damage_report.get("severity", 0))

    report = ReportGenerator.create_report(
        feedback=feedback,
        sentiment=sentiment,
        damage_analysis=damage_report,
    )

    # 5. ⭐ Upsert: update the open report, or insert a new one
    try:
        if existing:
            # Keep the same tracking_id / short_id, overwrite the rest
            tracking_id = update_damage_report(
                tracking_id=str(existing["tracking_id"]),
                feedback=feedback,
                sentiment=sentiment,
                sentiment_score=score,
                damage_severity=severity,
                damage_details=damage_report,
                damaged_image_path=damaged_path,
            )
            updated = True
            logger.info(f"[create_damage_report] updated existing report {tracking_id}")
        else:
            tracking_id = insert_damage_report(
                order_id=order_id,
                feedback=feedback,
                sentiment=sentiment,
                sentiment_score=score,
                damage_severity=severity,
                damage_details=damage_report,
                damaged_image_path=damaged_path,
                status="open",
            )
            updated = False
            logger.info(f"[create_damage_report] created new report {tracking_id}")
    except DatabaseError as e:
        # A race condition: two tabs submitted at the same time and both saw "no open report"
        msg = str(e).lower()
        if "uniq_open_report_per_order" in msg or "duplicate key" in msg:
            raise HTTPException(
                status_code=409,
                detail="Another submission just came in for this order. Please refresh and try again.",
            )
        db_fail("create_damage_report:upsert", e)

    return {
        "proceed": True,
        "tracking_id": tracking_id,
        "updated": updated,             # ← frontend can show "Report updated"
        "sentiment": sentiment,
        "score": score,
        "damage_severity": severity,
        "affected_area_percentage": damage_report.get("affected_area_percentage"),
        "recommendation": damage_report.get("recommendation"),
        "damaged_image_url": image_url(damaged_path),
    }

# ═══════════════════════════════════════════════════════
#  API: Track Report
# ═══════════════════════════════════════════════════════
@app.get("/api/reports/{tracking_id}")
async def track_report(tracking_id: str):
    tracking_id = tracking_id.strip().upper()

    if not REPORT_ID_RE.match(tracking_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid tracking ID format. Tracking IDs look like 'RPT-A3K9M2'.",
        )

    try:
        report = get_report_by_short_id(tracking_id)
    except DatabaseError as e:
        db_fail("track_report", e)

    if not report:
        raise HTTPException(status_code=404,
                            detail=f"No report found with tracking ID '{tracking_id}'.")

    return {
        "tracking_id": report["short_id"],
        "order_id": report["order_id"],
        "status": report["status"],
        "sentiment": report["sentiment"],
        "sentiment_score": float(report["sentiment_score"]),
        "damage_severity": float(report["damage_severity"]),
        "created_at": report["created_at"].isoformat(),
        "damaged_image_url": image_url(report.get("damaged_image_path")),
    }


# ═══════════════════════════════════════════════════════
#  API: Claim Warranty
# ═══════════════════════════════════════════════════════
@app.post("/api/warranty-claim")
async def create_warranty_claim(
    order_id: str = Form(...),
    reason: str = Form(...),
    image: UploadFile = File(...),
):
    order_id = order_id.strip()
    reason = reason.strip()

    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID is required.")
    if not reason:
        raise HTTPException(status_code=400, detail="Description of the incident is required.")

    processor = WarrantyClaimProcessor()
    eligible, product, why = processor.check_eligibility(order_id)
    if not eligible:
        raise HTTPException(status_code=400, detail=why)

    try:
        damaged_path = save_upload(image, DAMAGED_DIR)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[create_warranty_claim] save error: {e}")
        raise HTTPException(status_code=500, detail="Could not save the uploaded image.")

    logger.info(f"[create_warranty_claim] saved image: {damaged_path}")

    try:
        damage_report = DamageAnalyzer().analyze_damage(damaged_path)
    except ImageProcessingError as e:
        logger.error(f"[create_warranty_claim] image error: {e}")
        raise HTTPException(status_code=400, detail="Could not process the image.")

    if "error" in damage_report:
        raise HTTPException(status_code=400, detail=damage_report["error"])

    severity = float(damage_report.get("severity", 0))
    if severity <= 0:
        raise HTTPException(status_code=400, detail="No visible damage detected in the image.")

    expiry = product.get("warranty_expiry_date")
    if expiry is None and product.get("purchase_date") and product.get("warranty_period_days"):
        expiry = product["purchase_date"] + timedelta(days=product["warranty_period_days"])

    policy_snapshot = {
        "warranty_status":      product["warranty_status"],
        "purchase_date":        str(product["purchase_date"]),
        "warranty_period_days": product.get("warranty_period_days"),
        "warranty_expiry_date": str(expiry) if expiry else None,
        "is_crt":               product["is_crt"],
        "checked_at":           date.today().isoformat(),
    }

    try:
        claim_id = processor.create_claim(
            order_id=order_id,
            reason=reason,
            image_path=damaged_path,
            damage_severity=severity,
            policy_snapshot=policy_snapshot,
            damaged_image_path=damaged_path,
        )
    except DatabaseError as e:
        db_fail("create_warranty_claim:insert", e)

    return {
        "claim_id": claim_id,
        "status": "submitted",
        "damage_severity": severity,
        "message": "Warranty claim submitted successfully.",
        "damaged_image_url": image_url(damaged_path),
    }


# ═══════════════════════════════════════════════════════
#  API: Track Claim
# ═══════════════════════════════════════════════════════
@app.get("/api/claims/{claim_id}")
async def track_claim(claim_id: str):
    claim_id = claim_id.strip().upper()

    if not CLAIM_ID_RE.match(claim_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid claim ID format. Claim IDs look like 'CLM-X8T4B1'.",
        )

    try:
        claim = get_warranty_claim_by_short_id(claim_id)
    except DatabaseError as e:
        db_fail("track_claim", e)

    if not claim:
        raise HTTPException(status_code=404, detail=f"No claim found with ID '{claim_id}'.")

    return {
        "claim_id": claim["short_id"],
        "order_id": claim["order_id"],
        "claim_type": claim["claim_type"],
        "status": claim["status"],
        "damage_severity": float(claim["damage_severity"]),
        "created_at": claim["created_at"].isoformat(),
        "damaged_image_url": image_url(claim.get("damaged_image_path")),
    }
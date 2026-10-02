# main.py
import sys
import logging
from datetime import date, timedelta

from utils.logger import setup_logger
from utils.exceptions import (
    AudioInputError,
    ImageProcessingError,
    FeedbackProcessingError,
    DatabaseError,
)
from utils.input_handler import get_user_input

from models.feedback_processor import FeedbackProcessor
from models.damage_analyzer import DamageAnalyzer
from models.report_generator import ReportGenerator
from models.warranty_claim_processor import WarrantyClaimProcessor

from config import NEGATIVE_THRESHOLD
from db import (
    get_product_by_order_id,
    insert_damage_report,
    get_report_by_tracking_id,
)


# ─────────────────────────────────────────────────────
#  FLOW 1 — Raise report (arrived damaged)
# ─────────────────────────────────────────────────────
def raise_report(logger):
    print("\n── Raise a New Damage Report (Arrived Damaged) ──")

    order_id = input("Enter your Order ID: ").strip()
    if not order_id:
        print("No Order ID provided. Returning to menu.")
        return

    try:
        product = get_product_by_order_id(order_id)
    except DatabaseError as e:
        logger.error(f"DB error fetching order {order_id}: {e}")
        print("Could not verify order right now. Please try again later.")
        return

    if not product:
        print(f"Order ID '{order_id}' not found. Please check and try again.")
        return

    if not product.get("is_crt"):
        print(f"Product '{product['product_name']}' is not eligible for CRT damage reporting.")
        return

    print(f"✔ Verified: {product['product_name']} (Order {order_id})")

    # ── Feedback (text or voice) ──
    try:
        feedback = get_user_input()
        if not feedback:
            logger.error("No feedback received")
            print("No feedback received. Returning to menu.")
            return
    except AudioInputError as e:
        logger.error(f"Audio input error: {e}")
        print(f"Error with audio input: {e}")
        return

    # ── Sentiment analysis ──
    try:
        feedback_processor = FeedbackProcessor()
        sentiment, score = feedback_processor.analyze_sentiment(feedback)
        logger.info(f"Sentiment analysis complete: {sentiment} ({score:.2f})")
        print(f"\nDetected Sentiment: {sentiment} (Score: {score:.2f})")
    except FeedbackProcessingError as e:
        logger.error(f"Feedback processing error: {e}")
        print(f"Error processing feedback: {e}")
        return

    if not (sentiment == "negative" and score < NEGATIVE_THRESHOLD):
        print("\nThank you for your feedback!")
        return

    if input("\nWould you like to submit a damage report? (yes/no): ").strip().lower() != "yes":
        print("Returning to menu.")
        return

    # ── Image + damage analysis ──
    image_path = input("\nPlease provide the path to the damage image: ").strip()
    if not image_path:
        print("Image path required. Returning to menu.")
        return

    try:
        damage_analyzer = DamageAnalyzer()
        damage_report = damage_analyzer.analyze_damage(image_path)
    except ImageProcessingError as e:
        logger.error(f"Image processing error: {e}")
        print(f"Error processing image: {e}")
        return

    if "error" in damage_report:
        logger.error(f"Damage analysis error: {damage_report['error']}")
        print(f"\nError analyzing damage: {damage_report['error']}")
        return

    # ── Show analysis ──
    severity = float(damage_report.get("severity", 0))
    print("\n📊 Damage Analysis Result:")
    print(f"   Severity          : {severity}")
    print(f"   Affected Area (%) : {damage_report.get('affected_area_percentage')}")
    print(f"   Recommendation    : {damage_report.get('recommendation')}")

    # ── Build report ──
    report = ReportGenerator.create_report(
        feedback=feedback,
        sentiment=sentiment,
        damage_analysis=damage_report,
    )

    # ── Persist report ONLY (no warranty side-effects here) ──
    try:
        tracking_id = insert_damage_report(
            order_id=order_id,
            feedback=feedback,
            sentiment=sentiment,
            sentiment_score=score,
            damage_severity=severity,
            damage_details=damage_report,
            status="open",
        )
    except DatabaseError as e:
        logger.error(f"Failed to persist report: {e}")
        print(f"❌ Could not save report: {e}")
        return

    logger.info(f"Report stored. Tracking ID: {tracking_id}")
    print("\n✅ Report generated successfully!")
    print(report)
    print(f"\n🔖 Your Tracking ID: {tracking_id}")
    print("   Keep this ID to track your report status later.")


# ─────────────────────────────────────────────────────
#  FLOW 2 — Track report
# ─────────────────────────────────────────────────────
def track_report(logger):
    print("\n── Track an Existing Report ──")
    tracking_id = input("Enter your Tracking ID: ").strip()
    if not tracking_id:
        print("No Tracking ID provided. Returning to menu.")
        return

    try:
        report = get_report_by_tracking_id(tracking_id)
    except DatabaseError as e:
        logger.error(f"DB error fetching report {tracking_id}: {e}")
        print("Could not fetch report right now. Please try again later.")
        return

    if not report:
        print(f"No report found with Tracking ID '{tracking_id}'.")
        return

    print("\n📋 Report Details")
    print("──────────────────────────────────")
    print(f"Tracking ID  : {report['tracking_id']}")
    print(f"Order ID     : {report['order_id']}")
    print(f"Status       : {report['status']}")
    print(f"Sentiment    : {report['sentiment']} ({report['sentiment_score']})")
    print(f"Damage Score : {report['damage_severity']}")
    print(f"Created At   : {report['created_at']}")


# ─────────────────────────────────────────────────────
#  FLOW 3 — Claim warranty (post-purchase, user-caused damage)
# ─────────────────────────────────────────────────────
def claim_warranty(logger):
    print("\n── Claim Warranty (Post-Purchase Damage) ──")

    order_id = input("Enter your Order ID: ").strip()
    if not order_id:
        print("No Order ID provided. Returning to menu.")
        return

    processor = WarrantyClaimProcessor()
    eligible, product, reason = processor.check_eligibility(order_id)

    if not eligible:
        print(f"❌ Warranty claim not possible: {reason}")
        logger.info(f"Warranty claim rejected for order {order_id}: {reason}")
        return

    print(f"✔ Warranty active for: {product['product_name']} (Order {order_id})")

    image_path = input("\nPath to the damage image: ").strip()
    if not image_path:
        print("Image path required. Returning to menu.")
        return

    print("\n🔍 Running damage analysis on the image...")
    try:
        damage_analyzer = DamageAnalyzer()
        damage_report = damage_analyzer.analyze_damage(image_path)
    except ImageProcessingError as e:
        logger.error(f"Image processing error: {e}")
        print(f"Error processing image: {e}")
        return

    print("\n📊 Damage Analysis Result:")
    print(f"   Severity          : {damage_report.get('severity')}")
    print(f"   Affected Area (%) : {damage_report.get('affected_area_percentage')}")
    print(f"   Recommendation    : {damage_report.get('recommendation')}")

    if "error" in damage_report:
        print(f"\n❌ Error analyzing damage: {damage_report['error']}")
        return

    severity = float(damage_report.get("severity", 0))
    if severity <= 0:
        print("\n❌ No visible damage detected in the image. Claim not possible.")
        return

    reason_text = input("\nBriefly describe how the damage occurred: ").strip()
    if not reason_text:
        print("Description required. Returning to menu.")
        return

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
            reason=reason_text,
            image_path=image_path,
            damage_severity=severity,
            policy_snapshot=policy_snapshot,
        )
    except DatabaseError as e:
        logger.error(f"Failed to create warranty claim: {e}")
        print(f"❌ Could not create claim: {e}")
        return

    logger.info(f"Warranty claim created: {claim_id}")
    print("\n✅ Warranty claim submitted successfully!")
    print(f"🔖 Your Claim ID: {claim_id}")
    print("   Status: submitted")
    print("   Keep this ID to check your claim status.")


# ─────────────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────────────
def main():
    logger = setup_logger()

    try:
        print("Welcome to Insight Bot - AI Feedback & Damage Analysis System")
        print("1. Raise a new damage report (arrived damaged)")
        print("2. Track an existing report")
        print("3. Claim warranty (post-purchase damage)")
        print("4. Exit")

        choice = input("\nSelect an option (1/2/3/4): ").strip()

        if choice == "1":
            raise_report(logger)
        elif choice == "2":
            track_report(logger)
        elif choice == "3":
            claim_warranty(logger)
        elif choice == "4":
            print("Goodbye!")
        else:
            print("Invalid option. Exiting.")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"An unexpected error occurred: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
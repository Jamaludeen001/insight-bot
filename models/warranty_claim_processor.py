# models/warranty_claim_processor.py
import logging
from datetime import date, timedelta

from db import (
    get_product_by_order_id,
    get_active_claim_for_order,
    insert_warranty_claim,
)
from utils.exceptions import DatabaseError

logger = logging.getLogger("insight_bot")


class WarrantyClaimProcessor:
    """Post-purchase warranty claims with per-product policy validation."""

    def check_eligibility(self, order_id: str):
        try:
            product = get_product_by_order_id(order_id)
        except DatabaseError as e:
            return False, None, f"Database error: {e}"

        if not product:
            return False, None, f"Order '{order_id}' not found."

        if not product.get("is_crt"):
            return False, product, "This product is not eligible for warranty claims (not CRT)."

        if product.get("warranty_status") != "active":
            return False, product, f"Warranty status is '{product['warranty_status']}'."

        expiry = product.get("warranty_expiry_date")
        if expiry is None and product.get("purchase_date") and product.get("warranty_period_days"):
            expiry = product["purchase_date"] + timedelta(days=product["warranty_period_days"])

        if expiry and date.today() > expiry:
            return False, product, (
                f"Warranty expired on {expiry.isoformat()} "
                f"(period: {product.get('warranty_period_days')} days)."
            )

        try:
            existing = get_active_claim_for_order(order_id)
        except DatabaseError as e:
            return False, product, f"Database error: {e}"

        if existing:
            return False, product, (
                f"Warranty already claimed for this product. "
                f"Existing Claim ID: {existing['short_id']} "
                f"(status: {existing['status']}, filed on {existing['created_at'].date()})."
            )

        return True, product, "Eligible"

    def create_claim(
        self,
        *,
        order_id: str,
        reason: str,
        image_path: str,
        damage_severity: float,
        policy_snapshot: dict,
        damaged_image_path: str | None = None,
    ) -> str:
        return insert_warranty_claim(
            order_id=order_id,
            claim_type="post_purchase",
            reason=reason,
            image_path=image_path,
            damage_severity=damage_severity,
            policy_snapshot=policy_snapshot,
            damaged_image_path=damaged_image_path,
            status="submitted",
        )
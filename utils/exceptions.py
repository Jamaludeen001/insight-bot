# utils/exceptions.py

class InsightBotError(Exception):
    """Base exception for all Insight Bot errors."""

class AudioInputError(InsightBotError):
    pass

class ImageProcessingError(InsightBotError):
    pass

class FeedbackProcessingError(InsightBotError):
    pass

# ── NEW ─────────────────────────────────────────────
class DatabaseError(InsightBotError):
    """Raised for any DB connection / query failure."""

class OrderNotFoundError(InsightBotError):
    """Raised when the supplied order_id does not exist."""

class ProductNotEligibleError(InsightBotError):
    """Raised when the product is not CRT (not eligible)."""
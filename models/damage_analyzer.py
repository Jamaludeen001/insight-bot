# models/damage_analyzer.py
"""
Single-image damage analysis using Canny edge detection.

severity = min(1.0, edge_pixel_ratio / SEVERITY_MAX_RATIO)
affected_area_percentage = edge_pixel_ratio * 100
"""

import cv2
import numpy as np
from pathlib import Path


CANNY_LOW          = 100
CANNY_HIGH         = 200
SEVERITY_MAX_RATIO = 0.10   # 10% edges → severity 1.0


def load_and_preprocess_image(image_path: str) -> np.ndarray:
    if not Path(image_path).exists():
        raise ValueError(f"Image not found: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Invalid or unreadable image: {image_path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def detect_edges(gray_image: np.ndarray) -> np.ndarray:
    return cv2.Canny(gray_image, CANNY_LOW, CANNY_HIGH)


def calculate_damage_metrics(edges: np.ndarray):
    damage_pixels = int(np.count_nonzero(edges))
    total_pixels  = edges.shape[0] * edges.shape[1]
    if total_pixels == 0:
        return 0.0, 0.0
    severity = min(1.0, damage_pixels / (total_pixels * SEVERITY_MAX_RATIO))
    affected_percentage = (damage_pixels / total_pixels) * 100.0
    return severity, affected_percentage


def _recommendation(severity: float) -> str:
    if severity < 0.2:
        return "Minimal or no visible damage detected."
    if severity < 0.5:
        return "Minor damage detected. Monitor condition."
    if severity < 0.75:
        return "Moderate damage detected. Consider inspection."
    return "Severe damage detected. Recommend replacement or repair."


class DamageAnalyzer:
    """Single-image damage analysis."""

    def analyze_damage(self, image_path: str) -> dict:
        try:
            gray = load_and_preprocess_image(image_path)
        except ValueError as e:
            return {"error": str(e)}

        edges = detect_edges(gray)
        severity, affected_pct = calculate_damage_metrics(edges)

        return {
            "severity":                 round(float(severity), 4),
            "affected_area_percentage": round(float(affected_pct), 4),
            "recommendation":           _recommendation(severity),
        }
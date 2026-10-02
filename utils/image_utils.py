import cv2
import numpy as np

def load_and_preprocess_image(image_path):
    """Load and preprocess image for damage analysis"""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Invalid image path")
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def detect_edges(gray_image):
    """Detect edges in the image"""
    return cv2.Canny(gray_image, 100, 200)

def calculate_damage_metrics(edges):
    """Calculate damage metrics from edge detection"""
    damage_pixels = np.count_nonzero(edges)
    total_pixels = edges.shape[0] * edges.shape[1]
    severity = min(1.0, damage_pixels / (total_pixels * 0.1))
    affected_percentage = (damage_pixels / total_pixels) * 100
    return severity, affected_percentage
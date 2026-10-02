import cv2
import numpy as np
from PIL import Image

class DamageAnalyzer:
    def analyze_damage(self, image_path):
        """
        Analyze damage from the provided image.
        Returns damage assessment report.
        """
        try:
            # Load and process image
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "Invalid image path", "severity": 0}
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Basic edge detection for damage assessment
            edges = cv2.Canny(gray, 100, 200)
            damage_pixels = np.count_nonzero(edges)
            
            # Calculate damage severity (simplified)
            total_pixels = edges.shape[0] * edges.shape[1]
            severity = min(1.0, damage_pixels / (total_pixels * 0.1))
            
            return {
                "severity": severity,
                "affected_area_percentage": (damage_pixels / total_pixels) * 100,
                "recommendation": self._get_recommendation(severity)
            }
        except Exception as e:
            return {"error": str(e), "severity": 0}
    
    def _get_recommendation(self, severity):
        if severity > 0.7:
            return "Severe damage detected. Immediate attention required."
        elif severity > 0.4:
            return "Moderate damage detected. Repair recommended."
        else:
            return "Minor damage detected. Monitor condition."
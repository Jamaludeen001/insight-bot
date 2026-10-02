import json
from datetime import datetime

class ReportGenerator:
    @staticmethod
    def create_report(feedback, sentiment, damage_analysis):
        """
        Generate a comprehensive report combining feedback and damage analysis.
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "feedback": {
                "text": feedback,
                "sentiment": sentiment
            },
            "damage_assessment": damage_analysis,
            "recommendation": damage_analysis.get("recommendation", "N/A")
        }
        
        return json.dumps(report, indent=2)
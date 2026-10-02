import os
from PIL import Image

def validate_image_file(image_path):
    """Validate if the image file exists and is a valid image"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
        
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")
        
    return True

def validate_feedback_text(text):
    """Validate feedback text input"""
    if not text or not isinstance(text, str):
        raise ValueError("Feedback text cannot be empty and must be a string")
    if len(text.strip()) < 3:
        raise ValueError("Feedback text must be at least 3 characters long")
    return True
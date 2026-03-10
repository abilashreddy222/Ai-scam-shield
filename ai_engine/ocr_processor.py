import os
import cv2
import pytesseract

class OCRProcessor:
    def __init__(self):
        # We assume tesseract is accessible in the system PATH
        pass
        
    def extract_text(self, image_path):
        if not os.path.exists(image_path):
            return ""
            
        try:
            # Read image using OpenCV
            img = cv2.imread(image_path)
            if img is None:
                return ""
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Extract text
            text = pytesseract.image_to_string(gray)
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            if "tesseract is not installed" in str(e).lower():
                return "Error: Tesseract OCR is not installed on this system. Please install Tesseract Windows Binary to enable image scanning."
            return f"Error: {str(e)}"

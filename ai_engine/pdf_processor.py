"""
PDF Scam Detection Module
Extracts text from PDFs and analyzes for fraud indicators
"""

import pdfplumber
import re
from typing import Tuple, List, Dict

class PDFProcessor:
    def __init__(self):
        self.scam_indicators = {
            "payment_requests": [
                r"processing fee", r"registration fee", r"deposit required",
                r"bank transfer", r"advance payment", r"pay \$", r"payment of",
                r"wire transfer", r"western union", r"money gram"
            ],
            "fake_offers": [
                r"unrealistic salary", r"guaranteed .*benefit", r"100% guaranteed",
                r"double your.*investment", r"risk-free", r"too good to be true"
            ],
            "urgency": [
                r"urgent", r"immediately", r"asap", r"don't delay", r"limited time",
                r"act now", r"expire", r"deadline"
            ],
            "impersonation": [
                r"(apple|amazon|google|microsoft|bank)\s+(?:official|verified|authorized)",
                r"ceo|director|manager\s+(offering|requesting)"
            ]
        }
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
    
    def analyze_pdf(self, pdf_path: str) -> Tuple[float, List[str], Dict]:
        """
        Analyze PDF for scam indicators
        Returns: (risk_score, reasons, analysis_details)
        """
        text = self.extract_text(pdf_path)
        
        if "Error" in text:
            return 0.0, ["Could not process PDF"], {}
        
        risk_score = 0.0
        reasons = []
        matches = {"payment_requests": [], "fake_offers": [], "urgency": [], "impersonation": []}
        
        # Check for payment requests
        for pattern in self.scam_indicators["payment_requests"]:
            if re.search(pattern, text, re.IGNORECASE):
                risk_score += 25
                matches["payment_requests"].append(pattern)
                reasons.append(f"Detected payment request language: '{pattern}'")
        
        # Check for fake offers
        for pattern in self.scam_indicators["fake_offers"]:
            if re.search(pattern, text, re.IGNORECASE):
                risk_score += 20
                matches["fake_offers"].append(pattern)
                reasons.append(f"Detected unrealistic offer language: '{pattern}'")
        
        # Check for urgency tactics
        urgent_matches = sum(1 for pattern in self.scam_indicators["urgency"] 
                           if re.search(pattern, text, re.IGNORECASE))
        if urgent_matches > 0:
            risk_score += urgent_matches * 10
            matches["urgency"].append(f"Found {urgent_matches} urgency indicators")
            reasons.append(f"Detected {urgent_matches} urgency-inducing phrases")
        
        # Check for impersonation
        for pattern in self.scam_indicators["impersonation"]:
            if re.search(pattern, text, re.IGNORECASE):
                risk_score += 30
                matches["impersonation"].append(pattern)
                reasons.append(f"Potential impersonation of legitimate company")
        
        # Check PDF structure issues
        num_pages = len(text.split("\n")) // 50  # Rough page estimate
        if num_pages <= 1 and len(text) < 500:
            risk_score += 10
            reasons.append("PDF appears suspiciously short (potential fake document)")
        
        risk_score = min(risk_score, 100.0)
        
        return risk_score, reasons, {
            "extracted_text_length": len(text),
            "pattern_matches": matches
        }

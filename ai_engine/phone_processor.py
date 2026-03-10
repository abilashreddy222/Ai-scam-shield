"""
Phone Number Analysis Module
Analyzes phone numbers for scam indicators and reputation
"""

import re
from typing import Tuple, List, Dict

class PhoneProcessor:
    def __init__(self):
        self.known_scam_patterns = {
            "free_voip": [r"^\+1242", r"^\+1246", r"^\+1264", r"^\+1268"],  # Bahamas, Barbados, etc.
            "premium_rate": [r"^1900", r"^1976"],
            "suspicious_formats": [r"^[9]{10}$", r"^[1]{10}$"]  # All same digits
        }
    
    def parse_phone(self, phone_number: str) -> Dict:
        """Parse and validate phone number format"""
        # Remove common separators
        cleaned = re.sub(r"[\s\-\(\)\.]+", "", phone_number)
        
        analysis = {
            "original": phone_number,
            "cleaned": cleaned,
            "is_valid": False,
            "country_code": None,
            "format": None
        }
        
        # Basic US/International validation
        if re.match(r"^\+?1[0-9]{10}$", cleaned):
            analysis["is_valid"] = True
            analysis["country_code"] = "US"
            analysis["format"] = "US"
        elif re.match(r"^\+[0-9]{10,15}$", cleaned):
            analysis["is_valid"] = True
            analysis["country_code"] = "International"
            analysis["format"] = "International"
        elif re.match(r"^[0-9]{10,15}$", cleaned):
            analysis["is_valid"] = True
            analysis["country_code"] = "Unknown"
            analysis["format"] = "Generic"
        
        return analysis
    
    def check_scam_patterns(self, phone_number: str) -> List[str]:
        """Check phone number against known scam patterns"""
        issues = []
        
        # Check for free VoIP services commonly used in scams
        for pattern in self.known_scam_patterns["free_voip"]:
            if re.match(pattern, phone_number):
                issues.append("Phone number uses international VoIP service (commonly used in scams)")
        
        # Check for premium rate numbers
        for pattern in self.known_scam_patterns["premium_rate"]:
            if re.match(pattern, phone_number):
                issues.append("Premium rate number (charges may apply)")
        
        # Check for suspicious patterns (all same digits)
        for pattern in self.known_scam_patterns["suspicious_formats"]:
            if re.match(pattern, phone_number):
                issues.append("Phone number has suspicious pattern (repeated digits)")
        
        return issues
    
    def calculate_reputation_score(self, phone_number: str, parsed: Dict) -> float:
        """Calculate reputation score for phone number"""
        score = 0.0
        
        # Start with base score based on format
        if not parsed["is_valid"]:
            score += 30
        
        # International numbers are slightly more suspicious
        if parsed["country_code"] == "International":
            score += 15
        
        # VoIP typically used in scams
        if self.check_scam_patterns(phone_number):
            score += 25
        
        # Check for additional suspicious indicators
        if len(parsed["cleaned"]) < 10 or len(parsed["cleaned"]) > 15:
            score += 20
        
        return min(score, 100.0)
    
    def analyze_phone(self, phone_number: str) -> Tuple[float, List[str], Dict]:
        """
        Complete phone number analysis
        Returns: (risk_score, reasons, analysis_details)
        """
        reasons = []
        details = {}
        
        # Parse phone number
        parsed = self.parse_phone(phone_number)
        details["parsed"] = parsed
        
        if not parsed["is_valid"]:
            reasons.append("Phone number format is invalid or unrecognized")
        
        # Check for scam patterns
        pattern_issues = self.check_scam_patterns(phone_number)
        if pattern_issues:
            reasons.extend(pattern_issues)
        
        # Calculate reputation score
        risk_score = self.calculate_reputation_score(phone_number, parsed)
        details["reputation_score"] = risk_score
        
        # Additional checks
        if len(parsed["cleaned"]) == 10 and parsed["cleaned"].startswith(("555", "911")):
            risk_score += 10
            reasons.append("Uses reserved or test phone number")
        
        # Check if number appears as placeholder
        if parsed["cleaned"] in ["1234567890", "9999999999", "0000000000"]:
            risk_score = 100.0
            reasons.append("Appears to be a placeholder/not a real phone number")
        
        risk_score = min(risk_score, 100.0)
        
        return risk_score, reasons, details
    
    def check_reputation_database(self, phone_number: str) -> Dict:
        """
        Check phone number against database of known scam numbers
        In production, this would query the database
        """
        return {
            "past_reports": 0,
            "is_flagged": False,
            "common_scam_type": None
        }

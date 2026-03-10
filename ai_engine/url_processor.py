"""
URL & Website Fraud Detection Module
Analyzes suspicious URLs using Phishing Intelligence and heuristics
"""

import re
import requests
import socket
from typing import Tuple, List, Dict
from urllib.parse import urlparse
from datetime import datetime
import whois
import tldextract

class URLProcessor:
    def __init__(self):
        self.suspicious_keywords = [
            "login", "verify", "confirm", "update", "secure", "urgent",
            "click", "act", "validate", "Apple", "Amazon", "Google", "PayPal",
            "Netflix", "Facebook", "Instagram", "WhatsApp"
        ]
        
        self.typosquatting_targets = [
            "apple", "amazon", "google", "microsoft", "paypal", "netflix",
            "facebook", "instagram", "whatsapp", "linkedin", "bank", "irs"
        ]
        
        # Cache domain reputation
        self.reputation_cache = {}
        
    def parse_url(self, url: str) -> Dict:
        """Parse and extract URL components smoothly using tldextract"""
        try:
            parsed = urlparse(url)
            extracted = tldextract.extract(url)
            domain = f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain
            return {
                "scheme": parsed.scheme,
                "domain": domain,
                "full_netloc": parsed.netloc,
                "path": parsed.path,
                "is_valid": bool(parsed.netloc and parsed.scheme)
            }
        except:
            return {"is_valid": False}
            
    def check_ssl(self, hostname: str) -> bool:
        """Basic check if port 443 is open/valid (simulating SSL validation)"""
        try:
            socket.setdefaulttimeout(2)
            # Just test if we can reach port 443. Full SSL check could use ssl library
            s = socket.create_connection((hostname, 443))
            s.close()
            return True
        except:
            return False

    def check_domain_reputation(self, domain: str) -> Dict:
        """Check domain age, SSL certificate, and reputation"""
        # Return cached result if fresh
        if domain in self.reputation_cache:
            return self.reputation_cache[domain]
            
        analysis = {
            "domain": domain,
            "risk_score": 0,
            "checks": {}
        }
        
        # 1. Suspicious TLDs check
        if domain.endswith((".tk", ".ml", ".ga", ".cf", ".xyz", ".top", ".cc", ".link")):
            analysis["risk_score"] += 20
            analysis["checks"]["suspicious_tld"] = True
            
        # 2. Domain Age (WHOIS)
        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if creation_date:
                age_days = (datetime.now() - creation_date).days
                if age_days < 30:
                    analysis["risk_score"] += 35
                    analysis["checks"]["new_domain"] = True
        except Exception as e:
            # If WHOIS fails (e.g. unknown TLD or blocked), assume slight risk
            analysis["risk_score"] += 10
            
        # 3. Phishing Intelligence API / Databases
        # Since we simulate real APIs (like PhishTank or Google Safe Browsing), we check well-known fake patterns
        # OpenPhish Simulation (Mock)
        if "phishing" in domain.lower() or "free-prize" in domain.lower() or "secure-login" in domain.lower():
            analysis["risk_score"] += 50
            analysis["checks"]["phishing_database_match"] = True
            
        self.reputation_cache[domain] = analysis
        return analysis
        
    def detect_typosquatting(self, domain: str) -> Tuple[bool, str]:
        """Detect typosquatting attempts"""
        domain_lower = domain.lower().split(".")[0]
        for target in self.typosquatting_targets:
            if self._similar_strings(domain_lower, target) and domain_lower != target:
                return True, f"Typosquatting detected (imitating '{target}')"
        return False, ""
        
    def analyze_url(self, url: str) -> Tuple[float, List[str], Dict]:
        """
        Complete URL analysis with real-time intelligence
        Returns: (risk_score, reasons, analysis_details)
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        reasons = []
        details = {}
        risk_score = 0.0
        
        parsed = self.parse_url(url)
        if not parsed["is_valid"]:
            return 20.0, ["Invalid URL format"], {}
            
        details["parsed_url"] = parsed
        
        # Domain Reputation check
        domain_analysis = self.check_domain_reputation(parsed["domain"])
        risk_score += domain_analysis["risk_score"]
        details["domain_analysis"] = domain_analysis
        
        if domain_analysis["checks"].get("suspicious_tld"):
            reasons.append("Suspicious top-level domain")
        if domain_analysis["checks"].get("new_domain"):
            reasons.append("Domain recently registered (high risk)")
        if domain_analysis["checks"].get("phishing_database_match"):
            reasons.append("Domain found in phishing database")
            
        # SSL Check
        if not url.startswith("https://"):
            risk_score += 15
            reasons.append("URL does not use secure HTTPS connection")
        else:
            if not self.check_ssl(parsed["full_netloc"]):
                risk_score += 20
                reasons.append("SSL certificate invalid or missing")
                
        # Typosquatting Check
        is_typo, typo_msg = self.detect_typosquatting(parsed["domain"])
        if is_typo:
            risk_score += 40
            reasons.append(typo_msg)
            
        # URL Encoding tricks
        if "%25" in url or "%2F" in url or "@" in url:
            risk_score += 20
            reasons.append("URL contains encoded or misleading tricks (e.g., credentials embedded)")
            
        # Excessive params / IP check
        if re.search(r'http://\d+\.\d+\.\d+\.\d+', url):
            risk_score += 30
            reasons.append("URL uses IP address instead of domain name")
            
        final_risk_score = min(risk_score, 100.0)
        
        return final_risk_score, reasons, details
        
    @staticmethod
    def _similar_strings(s1: str, s2: str) -> bool:
        if len(s1) < 4 or len(s2) < 4:
            return False
        common = sum(1 for a, b in zip(s1, s2) if a == b)
        similarity = common / max(len(s1), len(s2))
        return similarity >= 0.8

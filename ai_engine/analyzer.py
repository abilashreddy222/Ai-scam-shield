import re
from typing import Tuple, List

# Common free email domains
FREE_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "protonmail.com", "live.com", "icloud.com"]

class MultiCategoryScamAnalyzer:
    """Enhanced analyzer supporting multiple scam categories"""
    
    def __init__(self, scam_keywords=None):
        self.scam_keywords = [kw.lower() for kw in (scam_keywords or [])]
        
        # Category-specific keywords
        self.category_keywords = {
            "Fake Job Scam": [
                "registration fee", "training fee", "processing fee", "deposit",
                "advance payment", "security amount", "immediate joining",
                "no interview", "direct selection", "work from home earning"
            ],
            "Phishing Email": [
                "verify account", "confirm password", "urgent action required",
                "suspended", "update information", "click here", "unusual activity",
                "verify identity"
            ],
            "Investment Scam": [
                "guaranteed returns", "double money", "risk-free", "massive profits",
                "limited slots", "secret strategy", "guaranteed", "get rich quick"
            ],
            "Loan Scam": [
                "loan approved", "instant loan", "no credit check", "processing fee",
                "advance payment", "admin charges", "guaranteed loan"
            ],
            "Lottery Scam": [
                "won a lottery", "claim prize", "lucky winner", "inheritance",
                "verification fee", "claim processing", "congratulations"
            ],
            "Crypto Scam": [
                "bitcoin", "cryptocurrency", "trading signals", "mining profits",
                "blockchain", "crypto exchange", "guaranteed returns"
            ],
            "E-commerce Scam": [
                "unbelievable discount", "luxury items", "authentic", "pay later",
                "refund policy", "unrealistic price", "fake product"
            ],
            "OTP Scam": [
                "share otp", "send otp", "verify otp", "otp required",
                "one time password"
            ]
        }
    
    def analyze_email(self, email: str) -> Tuple[float, List[str]]:
        """Analyze email for suspicious patterns"""
        if not email:
            return 0.0, []
        
        reasons = []
        score_penalty = 0.0
        email = email.strip().lower()
        
        # Check for free email domains
        if "@" in email:
            domain = email.split("@")[1]
            if domain in FREE_EMAIL_DOMAINS:
                reasons.append(f"Recruiter email uses a free/generic domain (@{domain}) instead of a corporate domain")
                score_penalty += 20.0
        
        # Check for suspicious email patterns
        if re.search(r"[0-9]{6,}|noreply|noreply", email):
            reasons.append("Email address contains suspicious patterns")
            score_penalty += 15.0
        
        return score_penalty, reasons
    
    def analyze_keywords(self, text: str) -> Tuple[float, List[str], List[str]]:
        """Analyze text for scam keywords"""
        if not text:
            return 0.0, [], []
        
        text_lower = text.lower()
        found_keywords = []
        
        for kw in self.scam_keywords:
            if kw in text_lower:
                found_keywords.append(kw)
        
        reasons = []
        score_penalty = 0.0
        
        if found_keywords:
            score_penalty += min(len(found_keywords) * 15.0, 60.0)
            reasons.append(f"Found {len(found_keywords)} suspicious keyword(s)")
        
        return score_penalty, found_keywords, reasons
    
    def analyze_language_patterns(self, text: str) -> Tuple[float, List[str]]:
        """Analyze text for suspicious language patterns"""
        if not text:
            return 0.0, []
        
        reasons = []
        score = 0.0
        text_lower = text.lower()
        
        # Urgency indicators
        urgency_patterns = r"\b(immediate|urgent|asap|now|today|instantly|immediately)\b"
        if re.search(urgency_patterns, text_lower):
            score += 15.0
            reasons.append("Uses urgency-inducing language")
        
        # Payment pressure
        payment_patterns = r"\b(pay|transfer|deposit|fee|charge|credit card|bank)\b"
        if re.search(payment_patterns, text_lower):
            score += 15.0
            reasons.append("Contains payment-related requests")
        
        # Excessive capitalization
        cap_letters = sum(1 for c in text if c.isupper())
        if cap_letters > len(text) * 0.3:
            score += 10.0
            reasons.append("Contains excessive CAPITALIZATION")
        
        # Multiple exclamation marks
        if text.count("!") > 3:
            score += 10.0
            reasons.append("Contains multiple exclamation marks")
        
        # Requests for personal information
        info_patterns = r"\b(password|ssn|credit card|account number|routing number|pin)\b"
        if re.search(info_patterns, text_lower):
            score += 25.0
            reasons.append("Requests sensitive personal information")
        
        return score, reasons
    
    def detect_scam_category(self, text: str) -> Tuple[str, float]:
        """Detect which category of scam this might be"""
        text_lower = text.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0.0
            matches = 0
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1.0
                    matches += 1
            
            # Normalize score
            if matches > 0:
                score = (matches / len(keywords)) * 100.0
            
            category_scores[category] = score
        
        # Find highest scoring category
        if max(category_scores.values()) > 0:
            top_category = max(category_scores, key=category_scores.get)
            top_score = category_scores[top_category]
            return top_category, top_score
        
        return "Unknown Suspicious Activity", 0.0
    
    def analyze_text(self, text: str) -> dict:
        """Comprehensive text analysis"""
        email_score, email_reasons = self.analyze_email(text)
        keyword_score, found_keywords, keyword_reasons = self.analyze_keywords(text)
        language_score, language_reasons = self.analyze_language_patterns(text)
        category, category_score = self.detect_scam_category(text)
        
        total_score = min(email_score + keyword_score + language_score, 100.0)
        
        all_reasons = email_reasons + keyword_reasons + language_reasons
        
        return {
            "total_score": total_score,
            "category": category,
            "category_score": category_score,
            "reasons": all_reasons if all_reasons else ["No suspicious patterns immediately found"],
            "keywords_found": found_keywords
        }

# Backward compatibility
class JobAnalyzer(MultiCategoryScamAnalyzer):
    """Legacy analyzer for backward compatibility"""
    pass

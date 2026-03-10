from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Multi-category scam reporting
class ReportedScam(db.Model):
    __tablename__ = 'reported_scam'
    
    id = db.Column(db.Integer, primary_key=True)
    scam_type = db.Column(db.String(50), nullable=False)  # Job, Phishing, Loan, Investment, etc.
    description = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    source_type = db.Column(db.String(50), nullable=False)  # text, image, pdf, url, email, phone, voice
    email = db.Column(db.String(120), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    analysis_details = db.Column(db.Text, nullable=True)  # JSON with detailed analysis
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Backward compatibility alias
ReportedJob = ReportedScam

class ScamKeyword(db.Model):
    __tablename__ = 'scam_keyword'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), unique=True, nullable=False)
    scam_category = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Phone number reputation tracking
class PhoneReputation(db.Model):
    __tablename__ = 'phone_reputation'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    report_count = db.Column(db.Integer, default=0)
    reputation_score = db.Column(db.Float, default=0.0)  # 0-100, higher = more suspicious
    scam_types = db.Column(db.Text, nullable=True)  # JSON array
    last_reported = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Domain reputation tracking
class DomainReputation(db.Model):
    __tablename__ = 'domain_reputation'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    risk_score = db.Column(db.Float, default=0.0)  # 0-100
    domain_age_days = db.Column(db.Integer, nullable=True)
    report_count = db.Column(db.Integer, default=0)
    is_typosquatting = db.Column(db.Boolean, default=False)
    ssl_certificate_valid = db.Column(db.Boolean, nullable=True)
    last_reported = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Suspicious URLs tracking
class SuspiciousURL(db.Model):
    __tablename__ = 'suspicious_url'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    scam_type = db.Column(db.String(50), nullable=False)
    detection_reason = db.Column(db.Text, nullable=True)
    report_count = db.Column(db.Integer, default=0)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Scam locations for map visualization
class ScamLocation(db.Model):
    __tablename__ = 'scam_location'
    
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    scam_type = db.Column(db.String(50), nullable=False)
    report_count = db.Column(db.Integer, default=0)
    recent_reports = db.Column(db.Text, nullable=True)  # JSON array
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

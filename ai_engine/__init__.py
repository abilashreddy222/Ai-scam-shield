"""
AI Engine Module
Multi-category scam detection using ML and rule-based analysis
"""

from .classifier import ScamClassifier, MultiCategoryScamClassifier
from .analyzer import JobAnalyzer, MultiCategoryScamAnalyzer
from .ocr_processor import OCRProcessor
from .pdf_processor import PDFProcessor
from .url_processor import URLProcessor
from .phone_processor import PhoneProcessor
from .voice_processor import VoiceProcessor

__all__ = [
    'ScamClassifier',
    'MultiCategoryScamClassifier',
    'JobAnalyzer',
    'MultiCategoryScamAnalyzer',
    'OCRProcessor',
    'PDFProcessor',
    'URLProcessor',
    'PhoneProcessor',
    'VoiceProcessor'
]

"""
Voice/Audio Scam Detection Module
Transcribes audio files and analyzes for scam indicators
"""

import os
from typing import Tuple, List, Dict
import re

class VoiceProcessor:
    def __init__(self):
        self.suspicious_phrases = {
            "urgency": [
                r"immediate|urgent|right now|asap|don't wait|act now|limited time",
                r"expire|deadline|hurry|today only|time running out"
            ],
            "payment_pressure": [
                r"payment|transfer|send money|western union|wire|credit card",
                r"account number|verify|confirm identity|ssn|social security",
                r"bank details|routing number"
            ],
            "impersonation": [
                r"(i'm|this is|calling from)\s*(apple|amazon|google|microsoft|irs|bank|police)",
                r"official|verify|authorized|representative|security team"
            ],
            "threats": [
                r"legal action|lawsuit|arrest|federal|crime|fine|penalty",
                r"problem|trouble|issue|suspended|disabled|locked|compromised"
            ]
        }
        
        self.try_import_providers()
    
    def try_import_providers(self):
        """Try to import available speech recognition providers"""
        self.sr_available = False
        self.whisper_available = False
        
        try:
            import speech_recognition as sr
            self.sr = sr
            self.sr_available = True
        except ImportError:
            pass
        
        try:
            import whisper
            self.whisper = whisper
            self.whisper_available = True
        except ImportError:
            pass
    
    def transcribe_audio(self, audio_path: str) -> Tuple[str, bool]:
        """
        Transcribe audio file to text
        Returns: (transcribed_text, success)
        """
        if not os.path.exists(audio_path):
            return f"File not found: {audio_path}", False
        
        # Try Whisper first (better accuracy)
        if self.whisper_available:
            try:
                model = self.whisper.load_model("base")
                result = model.transcribe(audio_path)
                return result.get("text", ""), True
            except Exception as e:
                return f"Whisper error: {str(e)}", False
        
        # Fallback to SpeechRecognition
        if self.sr_available:
            try:
                recognizer = self.sr.Recognizer()
                with self.sr.AudioFile(audio_path) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio)
                    return text, True
            except Exception as e:
                return f"Speech Recognition error: {str(e)}", False
        
        return "No audio processing library available. Install 'openai-whisper' or 'SpeechRecognition'.", False
    
    def analyze_transcription(self, text: str) -> Tuple[float, List[str]]:
        """Analyze transcribed text for scam indicators"""
        risk_score = 0.0
        reasons = []
        
        text_lower = text.lower()
        
        # Check for urgency tactics
        urgency_count = 0
        for pattern in self.suspicious_phrases["urgency"]:
            if re.search(pattern, text_lower):
                urgency_count += 1
        
        if urgency_count > 0:
            risk_score += urgency_count * 12
            reasons.append(f"Detected {urgency_count} urgency-inducing phrases")
        
        # Check for payment pressure
        payment_count = 0
        for pattern in self.suspicious_phrases["payment_pressure"]:
            if re.search(pattern, text_lower):
                payment_count += 1
        
        if payment_count > 0:
            risk_score += payment_count * 15
            reasons.append(f"Detected {payment_count} suspicious payment-related phrases")
        
        # Check for impersonation
        for pattern in self.suspicious_phrases["impersonation"]:
            if re.search(pattern, text_lower):
                risk_score += 25
                reasons.append("Caller impersonating legitimate organization")
        
        # Check for threats
        threat_count = 0
        for pattern in self.suspicious_phrases["threats"]:
            if re.search(pattern, text_lower):
                threat_count += 1
        
        if threat_count > 0:
            risk_score += threat_count * 18
            reasons.append(f"Detected {threat_count} threatening phrases")
        
        # Check for number requests
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|ssn|social security|account|routing|credit card', text_lower):
            risk_score += 20
            reasons.append("Caller requesting personal or financial information")
        
        risk_score = min(risk_score, 100.0)
        
        return risk_score, reasons
    
    def analyze_voice(self, audio_path: str) -> Tuple[float, List[str], Dict]:
        """
        Complete voice analysis pipeline
        Returns: (risk_score, reasons, analysis_details)
        """
        details = {}
        
        # Check file exists
        if not os.path.exists(audio_path):
            return 0.0, [f"Audio file not found: {audio_path}"], {}
        
        # Transcribe audio
        transcription, success = self.transcribe_audio(audio_path)
        
        if not success:
            return 0.0, [f"Could not transcribe audio: {transcription}"], {
                "transcription_error": transcription
            }
        
        details["transcription"] = transcription
        details["transcription_length"] = len(transcription.split())
        
        # Analyze transcription
        risk_score, reasons = self.analyze_transcription(transcription)
        
        # Additional checks
        if len(transcription) < 20:
            reasons.append("Audio too short to analyze properly")
        
        if len(transcription) > 5000:
            reasons.append("Audio processing may be incomplete")
        
        return risk_score, reasons, details

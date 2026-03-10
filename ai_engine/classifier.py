import os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
from typing import Tuple, List, Dict
import threading

class ScamDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

class MultiCategoryScamClassifier:
    """BERT-based Multi-category scam classifier supporting 9 scam types"""
    
    SCAM_CATEGORIES = [
        "Fake Job Scam",
        "Phishing Email",
        "Investment Scam",
        "Loan Scam",
        "Lottery Scam",
        "Crypto Scam",
        "E-commerce Scam",
        "OTP Scam",
        "Legitimate"
    ]
    
    def __init__(self):
        self.model_name = "distilbert-base-uncased"
        self.model_dir = "instance/scam_bert_model"
        
        self.id2label = {i: label for i, label in enumerate(self.SCAM_CATEGORIES)}
        self.label2id = {label: i for i, label in enumerate(self.SCAM_CATEGORIES)}
        
        self.model = None
        self.is_ready = False
        
        # Determine device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Start model loading in the background
        threading.Thread(target=self._initialize_model, daemon=True).start()
        
    def _initialize_model(self):
        """Loads or trains the model asynchronously to prevent server blocking"""
        print("Loading AI Model in background...")
        # Setup tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Load or train model
        if os.path.exists(self.model_dir):
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir).to(self.device)
            except Exception as e:
                print(f"Error loading model from {self.model_dir}: {e}. Retraining...")
                self._train_model()
        else:
            self._train_model()
            
        self.model.eval()
        self.is_ready = True
        print("AI Model is fully loaded and ready!")
            
    def _train_model(self):
        """Fine-tunes the BERT model for scam classification"""
        print("Initializing BERT Training. This may take a moment...")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name, 
            num_labels=len(self.SCAM_CATEGORIES),
            id2label=self.id2label,
            label2id=self.label2id
        ).to(self.device)
        
        # Expanded Training data
        training_data = {
            "Fake Job Scam": [
                "pay registration fee to start working",
                "immediate joining, deposit security amount required",
                "work from home earning big money, training fee required",
                "no interview, direct selection, processing fee needed",
                "job offer requires advance payment for processing",
                "urgent hiring, deposit for background check",
                "earn money instantly, pay deposit first"
            ],
            "Phishing Email": [
                "verify your account immediately or it will be suspended",
                "confirm your password by clicking this link",
                "update your payment information to avoid account closure",
                "unusual activity detected, verify your identity",
                "click here to update your account security",
                "confirm your personal information immediately",
                "unusual login attempt, change your password now"
            ],
            "Investment Scam": [
                "guaranteed returns of 50% per month",
                "double your investment in 30 days",
                "risk-free investment opportunity with massive profits",
                "secret investment strategy, limited slots available",
                "guaranteed 100% profit, no risk involved",
                "invest now, get rich quick scheme"
            ],
            "Loan Scam": [
                "loan approved instantly, pay processing fee",
                "get personal loan in 24 hours, advance payment required",
                "no credit check loan, deposit money first",
                "urgent cash needed, processing fee applies",
                "loan guaranteed, admin charges upfront"
            ],
            "Lottery Scam": [
                "congratulations, you have won a lottery",
                "claim your prize now, small verification fee required",
                "you are the lucky winner, verify to collect cash",
                "lucky draw selected you, pay claim processing fee",
                "inheritance money waiting, claim procedure fee"
            ],
            "Crypto Scam": [
                "bitcoin investment guaranteed returns",
                "crypto trading signals, sure profit system",
                "join our crypto exchange, make money daily",
                "blockchain opportunity, limited time offer",
                "crypto mining profits, deposit to start"
            ],
            "E-commerce Scam": [
                "unbelievable discount on luxury items",
                "authenticity not guaranteed, unrealistic price",
                "buy now, pay later scheme with hidden charges",
                "fake product listing with unrealistic claims",
                "best price guaranteed, refund policy unknown"
            ],
            "OTP Scam": [
                "share your otp for verification",
                "send otp to complete your transaction",
                "provide your otp to confirm identity",
                "otp required for account update"
            ],
            "Legitimate": [
                "we are hiring software engineers, apply on our career portal",
                "meeting scheduled for tomorrow at 10 am",
                "your order has been successfully delivered",
                "please find attached the project report",
                "let's catch up over coffee next week",
                "your monthly statement is ready to view online",
                "thank you for your purchase from our official store"
            ]
        }
        
        texts = []
        labels = []
        for category, samples in training_data.items():
            for text in samples:
                texts.append(text)
                labels.append(self.label2id[category])
                
        encodings = self.tokenizer(texts, truncation=True, padding=True, max_length=128)
        dataset = ScamDataset(encodings, labels)
        
        training_args = TrainingArguments(
            output_dir='./results',
            num_train_epochs=3,
            per_device_train_batch_size=8,
            warmup_steps=10,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=10,
            save_strategy="no"
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
        )
        
        trainer.train()
        
        # Save model
        os.makedirs(os.path.dirname(self.model_dir), exist_ok=True)
        self.model.save_pretrained(self.model_dir)
        self.tokenizer.save_pretrained(self.model_dir)
        print("Model fine-tuning complete and saved!")

    def predict(self, text: str) -> Dict:
        """
        Predict scam category and confidence using BERT
        Returns the specific format requested.
        """
        if not self.is_ready:
            return {
                "scam_type": "AI Model Loading",
                "risk_score": 0,
                "confidence": 0.0,
                "reasons": ["The AI classification model is still initializing in the background. Please wait a few seconds and try again."]
            }
            
        if not text or len(text.strip()) == 0:
            return {
                "scam_type": "Legitimate",
                "risk_score": 0,
                "confidence": 1.0,
                "reasons": []
            }
            
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=256).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Compute Softmax
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, predicted_class_id = torch.max(probabilities, dim=-1)
            
            scam_type = self.id2label[predicted_class_id.item()]
            confidence_val = confidence.item()
            
            # Risk score derived from model probability
            if scam_type == "Legitimate":
                risk_score = (1.0 - confidence_val) * 100
            else:
                risk_score = confidence_val * 100
                
            reasons = self._generate_reasons(text, scam_type, risk_score)
            
            return {
                "scam_type": scam_type,
                "risk_score": round(max(0, min(100, risk_score)), 1),
                "confidence": round(confidence_val, 2),
                "reasons": reasons
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                "scam_type": "Unknown Suspicious Activity",
                "risk_score": 50,
                "confidence": 0.5,
                "reasons": ["Error during model inference"]
            }
            
    def _generate_reasons(self, text: str, scam_type: str, risk_score: float) -> List[str]:
        """Generate specific detection reasons based on text patterns and category"""
        reasons = []
        text_lower = text.lower()
        
        if scam_type == "Legitimate":
            if risk_score > 20:
                reasons.append("Slightly irregular language but mostly safe.")
            return reasons
            
        # Basic rule-matching to provide tangible reasons
        if "fee" in text_lower or "deposit" in text_lower or "payment" in text_lower:
            reasons.append("Requests for upfront payment or deposit detected")
        if "immediate" in text_lower or "urgent" in text_lower:
            reasons.append("Urgency-inducing language designed to pressure you")
        if "guaranteed" in text_lower or "risk-free" in text_lower:
            reasons.append("Unrealistic promises of guaranteed returns/success")
        if "otp" in text_lower or "password" in text_lower:
            reasons.append("Requests for sensitive authentication information")
        if "verify" in text_lower or "suspended" in text_lower:
            reasons.append("Common phishing tactic (account verification/suspension)")
            
        if not reasons:
            reasons.append(f"Model detected strong patterns associated with {scam_type}")
            
        return reasons

# Backward compatibility
class ScamClassifier(MultiCategoryScamClassifier):
    pass

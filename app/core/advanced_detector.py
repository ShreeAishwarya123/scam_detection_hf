import re
import torch
import numpy as np
from typing import Dict, List, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

class AdvancedScamDetector:
    def __init__(self):
        # Load multiple models for ensemble
        self.models = self._load_models()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.ensemble_model = None
        self._load_ensemble_model()
        
        # Advanced scam patterns
        self.scam_patterns = {
            'urgency': r'\b(urgent|immediate|asap|hurry|quick|fast|instant|now|today|before it\'s too late)\b',
            'authority': r'\b(bank|paypal|amazon|google|microsoft|apple|facebook|instagram|government|police|court|irs|fbi)\b',
            'financial': r'\b(money|payment|transfer|deposit|withdrawal|invoice|bill|account|credit|debit|wallet|upi|paytm|phonepe|gpay)\b',
            'threat': r'\b(suspend|block|close|delete|arrest|legal|lawsuit|jail|fine|penalty|prosecute)\b',
            'prize': r'\b(winner|prize|lottery|gift|reward|bonus|congratulations|claim|free|cash|million|billion)\b',
            'personal_info': r'\b(ssn|pan|aadhaar|password|otp|pin|cvv|account number|card number|verification)\b',
            'links': r'https?://[^\s]+',
            'phone': r'(\+91|0)?[6-9]\d{9}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'upi': r'[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}',
        }
        
        # Scam severity weights
        self.severity_weights = {
            'urgency': 0.3,
            'authority': 0.25,
            'financial': 0.2,
            'threat': 0.35,
            'prize': 0.25,
            'personal_info': 0.4,
            'links': 0.3,
            'phone': 0.15,
            'email': 0.1,
            'upi': 0.2,
        }
    
    def _load_models(self):
        """Load multiple BERT models for ensemble"""
        models = {}
        model_configs = [
            {
                'name': 'bert_base',
                'model': 'bert-base-uncased',
                'tokenizer': 'bert-base-uncased'
            },
            {
                'name': 'distilbert',
                'model': 'distilbert-base-uncased',
                'tokenizer': 'distilbert-base-uncased'
            },
            {
                'name': 'roberta',
                'model': 'roberta-base',
                'tokenizer': 'roberta-base'
            }
        ]
        
        for config in model_configs:
            try:
                tokenizer = AutoTokenizer.from_pretrained(config['tokenizer'])
                model = AutoModelForSequenceClassification.from_pretrained(config['model'])
                models[config['name']] = {'tokenizer': tokenizer, 'model': model}
                print(f"✅ Loaded {config['name']} model")
            except Exception as e:
                print(f"⚠️ Could not load {config['name']}: {e}")
        
        return models
    
    def _load_ensemble_model(self):
        """Load or train ensemble model"""
        ensemble_path = 'app/models/ensemble_model.pkl'
        if os.path.exists(ensemble_path):
            with open(ensemble_path, 'rb') as f:
                self.ensemble_model = pickle.load(f)
        else:
            # Create simple ensemble model
            self.ensemble_model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    def extract_features(self, text: str) -> Dict:
        """Extract advanced features from text"""
        features = {}
        text_lower = text.lower()
        
        # Pattern-based features
        for pattern_name, pattern in self.scam_patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            features[f'{pattern_name}_count'] = len(matches)
            features[f'{pattern_name}_present'] = 1 if matches else 0
        
        # Text-based features
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        features['uppercase_ratio'] = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        features['digit_ratio'] = sum(1 for c in text if c.isdigit()) / len(text) if text else 0
        
        # Suspicious indicators
        features['has_urgent_words'] = 1 if re.search(r'\b(urgent|immediate|asap)\b', text_lower) else 0
        features['has_authority_impersonation'] = 1 if re.search(r'\b(bank|paypal|amazon|google|microsoft)\b', text_lower) else 0
        features['has_financial_request'] = 1 if re.search(r'\b(send|transfer|pay|deposit)\b', text_lower) else 0
        features['has_threat'] = 1 if re.search(r'\b(suspend|block|arrest|legal)\b', text_lower) else 0
        
        return features
    
    def calculate_severity_score(self, features: Dict) -> float:
        """Calculate scam severity score"""
        severity = 0.0
        for pattern_name, weight in self.severity_weights.items():
            if f'{pattern_name}_present' in features:
                severity += features[f'{pattern_name}_present'] * weight
        
        return min(severity, 1.0)  # Cap at 1.0
    
    def get_model_predictions(self, text: str) -> Dict:
        """Get predictions from multiple models"""
        predictions = {}
        
        for model_name, model_data in self.models.items():
            try:
                tokenizer = model_data['tokenizer']
                model = model_data['model']
                
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = torch.softmax(outputs.logits, dim=1)
                    confidence = probs.max().item()
                    prediction = probs.argmax().item()
                
                predictions[model_name] = {
                    'prediction': prediction,
                    'confidence': confidence
                }
            except Exception as e:
                print(f"Error in {model_name}: {e}")
                predictions[model_name] = {'prediction': 0, 'confidence': 0.0}
        
        return predictions
    
    def ensemble_predict(self, text: str) -> Dict:
        """Make ensemble prediction"""
        # Get individual model predictions
        model_preds = self.get_model_predictions(text)
        
        # Extract features for ensemble
        features = self.extract_features(text)
        feature_vector = np.array(list(features.values())).reshape(1, -1)
        
        # Get ensemble prediction (simplified)
        avg_confidence = np.mean([pred['confidence'] for pred in model_preds.values()])
        avg_prediction = np.mean([pred['prediction'] for pred in model_preds.values()])
        
        # Calculate severity
        severity = self.calculate_severity_score(features)
        
        # Final decision logic
        final_prediction = 1 if (avg_prediction > 0.5 or severity > 0.3) else 0
        final_confidence = max(avg_confidence, severity)
        
        return {
            'is_scam': bool(final_prediction),
            'confidence': float(final_confidence),
            'severity': float(severity),
            'features': features,
            'model_predictions': model_preds,
            'detected_patterns': [k for k, v in features.items() if k.endswith('_present') and v == 1]
        }
    
    def get_detailed_analysis(self, text: str) -> Dict:
        """Get comprehensive scam analysis"""
        result = self.ensemble_predict(text)
        
        # Add scam type classification
        scam_types = []
        features = result['features']
        
        if features.get('urgency_present', 0):
            scam_types.append('Urgency Scam')
        if features.get('authority_present', 0):
            scam_types.append('Authority Impersonation')
        if features.get('prize_present', 0):
            scam_types.append('Prize/Lottery Scam')
        if features.get('threat_present', 0):
            scam_types.append('Threat/Extortion')
        if features.get('financial_present', 0):
            scam_types.append('Financial Fraud')
        
        result['scam_types'] = scam_types
        result['risk_level'] = self._get_risk_level(result['severity'])
        
        return result
    
    def _get_risk_level(self, severity: float) -> str:
        """Determine risk level based on severity"""
        if severity >= 0.7:
            return 'HIGH'
        elif severity >= 0.4:
            return 'MEDIUM'
        elif severity >= 0.2:
            return 'LOW'
        else:
            return 'VERY_LOW'

# Global instance
advanced_detector = AdvancedScamDetector()

def detect_scam_advanced(text: str) -> Dict:
    """Advanced scam detection function"""
    return advanced_detector.get_detailed_analysis(text)

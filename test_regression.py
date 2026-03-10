import unittest
import json
import os
from app import app, db
from ai_engine.url_processor import URLProcessor

class ScamShieldRegressionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the test client and initialize the database."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.client = app.test_client()

        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Clean up the database."""
        with app.app_context():
            db.drop_all()

    def test_01_health_check(self):
        """Test if the main application routes are loading correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/admin')
        # Should redirect to login (302)
        self.assertEqual(response.status_code, 302)

    def test_02_url_analyzer_api(self):
        """Test the URL analysis endpoint (Real-time Phishing Intel)."""
        payload = {"url": "http://example.com"}
        response = self.client.post('/api/analyze/url', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify the structure of the JSON response
        self.assertIn("risk_score", data)
        self.assertIn("reasons", data)
        self.assertIn("details", data)
        self.assertTrue(isinstance(data["risk_score"], (int, float)))

    def test_03_text_analyzer_api_missing_data(self):
        """Test text analysis endpoint error handling."""
        payload = {"text": ""}
        response = self.client.post('/api/analyze/text', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Text cannot be empty", response.data)

    def test_04_url_processor_logic(self):
        """Test the standalone URL processor logic skips empty URLs."""
        url_proc = URLProcessor()
        # Test suspicious TLD logic directly
        risk, reasons, details = url_proc.analyze_url("http://paypal-secure.tk")
        # .tk is a known suspicious TLD, should trigger risk
        self.assertTrue(risk > 0)
        self.assertTrue(any("Suspicious top-level domain" in r for r in reasons))

if __name__ == '__main__':
    print("="*60)
    print("AI SCAM SHIELD - AUTOMATED REGRESSION TEST SUITE")
    print("="*60)
    unittest.main(verbosity=2)

import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import csv
from io import StringIO
from flask import make_response
from database import db, ReportedScam, ScamKeyword, PhoneReputation, DomainReputation, SuspiciousURL, ScamLocation
from ai_engine.classifier import ScamClassifier, MultiCategoryScamClassifier
from ai_engine.analyzer import JobAnalyzer, MultiCategoryScamAnalyzer
from ai_engine.ocr_processor import OCRProcessor
from ai_engine.pdf_processor import PDFProcessor
from ai_engine.url_processor import URLProcessor
from ai_engine.phone_processor import PhoneProcessor
from ai_engine.voice_processor import VoiceProcessor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scam_detection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'img', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Initialize AI models (lazy loading)
classifier = None
legacy_classifier = None
ocr_processor = None
pdf_processor = None
url_processor = None
phone_processor = None
voice_processor = None

def get_classifier():
    global classifier
    if classifier is None:
        classifier = MultiCategoryScamClassifier()
    return classifier

def get_legacy_classifier():
    global legacy_classifier
    if legacy_classifier is None:
        legacy_classifier = ScamClassifier()
    return legacy_classifier

def get_ocr_processor():
    global ocr_processor
    if ocr_processor is None:
        ocr_processor = OCRProcessor()
    return ocr_processor

def get_pdf_processor():
    global pdf_processor
    if pdf_processor is None:
        pdf_processor = PDFProcessor()
    return pdf_processor

def get_url_processor():
    global url_processor
    if url_processor is None:
        url_processor = URLProcessor()
    return url_processor

def get_phone_processor():
    global phone_processor
    if phone_processor is None:
        phone_processor = PhoneProcessor()
    return phone_processor

def get_voice_processor():
    global voice_processor
    if voice_processor is None:
        voice_processor = VoiceProcessor()
    return voice_processor

def cleanup_file(filepath):
    """Safely remove uploaded file after processing"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Warning: Could not remove file {filepath}: {e}")

def allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

with app.app_context():
    try:
        db.create_all()
        # Only add default keywords if table is empty
        if ScamKeyword.query.count() == 0:
            default_keywords = [
                "pay registration fee", "training deposit required", 
                "processing charges", "immediate joining without interview", 
                "work from home earning", "security deposit",
                "guaranteed returns", "double your money", "claim prize",
                "verify account", "confirm password", "update information"
            ]
            for kw in default_keywords:
                db.session.add(ScamKeyword(keyword=kw))
            db.session.commit()
            print("Database initialized with default keywords")
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue without failing - tables might already exist

# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Login page for admin portal"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Determine credentials (prefer env vars, fallback to default)
        admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if username == admin_user and password == admin_pass:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials. Please try again.", "error")
            
    return render_template('admin_login.html')

@app.route('/admin-logout')
def admin_logout():
    """Logout admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    reports = ReportedScam.query.order_by(ReportedScam.created_at.desc()).all()
    keywords = ScamKeyword.query.all()
    return render_template('admin.html', reports=reports, keywords=keywords)

@app.route('/map')
def scam_map():
    """Scam activity visualization map"""
    return render_template('map.html')

@app.route('/assistant')
def assistant():
    """AI Scam Assistant chatbot"""
    return render_template('assistant.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/analyze/text', methods=['POST'])
def analyze_text():
    """Analyze text for scams"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        email = data.get('email', '').strip()
        
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        # Get keywords from database
        db_keywords = [k.keyword for k in ScamKeyword.query.all()]
        analyzer = MultiCategoryScamAnalyzer(db_keywords)
        
        # Comprehensive analysis
        analysis = analyzer.analyze_text(text)
        
        # ML Model Prediction
        prediction = get_classifier().predict(text)
        category = prediction["scam_type"]
        confidence = prediction["confidence"]
        ml_score = prediction["risk_score"]
        
        # Email analysis
        email_score, email_reasons = analyzer.analyze_email(email)
        
        # Combine scores
        total_score = min((analysis['total_score'] + email_score + ml_score) / 2 if email else (analysis['total_score'] + ml_score) / 2, 100.0)
        
        all_reasons = analysis['reasons'] + email_reasons + prediction["reasons"]
        
        result = {
            "scam_type": category,
            "risk_score": round(total_score, 1),
            "confidence": round(confidence * 100, 1),
            "category_confidence": round(analysis['category_score'], 1),
            "reasons": list(set(all_reasons)),
            "keywords_found": analysis['keywords_found']
        }
        
        # Save to database
        report = ReportedScam(
            scam_type=category,
            description=text[:500],
            risk_score=total_score,
            confidence=confidence,
            source_type="text",
            email=email if email else None,
            analysis_details=json.dumps(result)
        )
        db.session.add(report)
        db.session.commit()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/image', methods=['POST'])
def analyze_image():
    """Analyze image/screenshot for scams"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'bmp'}):
            return jsonify({"error": "Invalid file type. Only images allowed"}), 400
        
        # Generate secure filename
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(filepath)
        
        try:
            # Extract text from image
            extracted_text = get_ocr_processor().extract_text(filepath)
            
            if "Error" in extracted_text:
                return jsonify({"error": "Could not process image", "details": extracted_text}), 400
            
            # Analyze extracted text
            db_keywords = [k.keyword for k in ScamKeyword.query.all()]
            analyzer = MultiCategoryScamAnalyzer(db_keywords)
            analysis = analyzer.analyze_text(extracted_text)
            
            # ML Model Prediction
            prediction = get_classifier().predict(extracted_text)
            category = prediction["scam_type"]
            confidence = prediction["confidence"]
            ml_score = prediction["risk_score"]
            
            total_score = min((analysis['total_score'] + ml_score) / 2, 100.0)
            all_reasons = analysis['reasons'] + prediction["reasons"]
            
            result = {
                "scam_type": category,
                "risk_score": round(total_score, 1),
                "confidence": round(confidence * 100, 1),
                "reasons": list(set(all_reasons)),
                "extracted_text": extracted_text[:1000],  # Return first 1000 chars
                "keywords_found": analysis['keywords_found']
            }
            
            # Save to database
            report = ReportedScam(
                scam_type=category,
                description=extracted_text[:500],
                risk_score=total_score,
                confidence=confidence,
                source_type="image",
                file_path=filepath,
                analysis_details=json.dumps(result)
            )
            db.session.add(report)
            db.session.commit()
            
            return jsonify(result)
        
        finally:
            # Always cleanup the uploaded file
            cleanup_file(filepath)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/pdf', methods=['POST'])
def analyze_pdf():
    """Analyze PDF document for scams"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        if not allowed_file(file.filename, {'pdf'}):
            return jsonify({"error": "File must be PDF"}), 400
        
        # Generate secure filename
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(filepath)
        
        try:
            # Analyze PDF
            pdf_risk_score, pdf_reasons, pdf_details = get_pdf_processor().analyze_pdf(filepath)
            
            # Extract and analyze text
            extracted_text = get_pdf_processor().extract_text(filepath)
            db_keywords = [k.keyword for k in ScamKeyword.query.all()]
            analyzer = MultiCategoryScamAnalyzer(db_keywords)
            analysis = analyzer.analyze_text(extracted_text)
            
            # ML Model Prediction
            prediction = get_classifier().predict(extracted_text)
            category = prediction["scam_type"]
            confidence = prediction["confidence"]
            ml_score = prediction["risk_score"]
            
            # Combine scores
            total_score = min((pdf_risk_score + analysis['total_score'] + ml_score) / 3, 100.0)
            
            all_reasons = pdf_reasons + analysis['reasons'] + prediction["reasons"]
            
            result = {
                "scam_type": category,
                "risk_score": round(total_score, 1),
                "confidence": round(confidence * 100, 1),
                "reasons": list(set(all_reasons)),
                "pdf_analysis": pdf_details,
                "keywords_found": analysis['keywords_found']
            }
            
            # Save to database
            report = ReportedScam(
                scam_type=category,
                description=extracted_text[:500],
                risk_score=total_score,
                confidence=confidence,
                source_type="pdf",
                file_path=filepath,
                analysis_details=json.dumps(result)
            )
            db.session.add(report)
            db.session.commit()
            
            return jsonify(result)
        
        finally:
            # Always cleanup the uploaded file
            cleanup_file(filepath)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/url', methods=['POST'])
def analyze_url():
    """Analyze URL for phishing and fraud"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "URL cannot be empty"}), 400
        
        # Analyze URL
        risk_score, reasons, details = get_url_processor().analyze_url(url)
        
        result = {
            "url": url,
            "risk_score": round(risk_score, 1),
            "reasons": reasons,
            "details": details
        }
        
        # Determine scam type
        if risk_score > 70:
            scam_type = "Phishing Email"
        elif risk_score > 40:
            scam_type = "Suspicious Website"
        else:
            scam_type = "Legitimate Website"
        
        # Save to database
        report = ReportedScam(
            scam_type=scam_type,
            description=url,
            risk_score=risk_score,
            source_type="url",
            url=url,
            analysis_details=json.dumps(result)
        )
        db.session.add(report)
        
        # Also save to SuspiciousURL table if risky
        if risk_score > 50:
            suspicious_url = SuspiciousURL(
                url=url,
                risk_score=risk_score,
                domain=details.get('parsed_url', {}).get('domain', ''),
                scam_type=scam_type,
                detection_reason='; '.join(reasons)
            )
            db.session.add(suspicious_url)
        
        db.session.commit()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/phone', methods=['POST'])
def analyze_phone():
    """Analyze phone number for scam indicators"""
    try:
        data = request.json
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify({"error": "Phone number cannot be empty"}), 400
        
        # Analyze phone
        risk_score, reasons, details = get_phone_processor().analyze_phone(phone)
        
        result = {
            "phone": phone,
            "risk_score": round(risk_score, 1),
            "reasons": reasons,
            "details": details
        }
        
        # Determine scam type
        if risk_score > 70:
            scam_type = "Suspicious Phone Number"
        else:
            scam_type = "Phone Verification"
        
        # Save to database
        report = ReportedScam(
            scam_type=scam_type,
            description=phone,
            risk_score=risk_score,
            source_type="phone",
            phone_number=phone,
            analysis_details=json.dumps(result)
        )
        db.session.add(report)
        
        # Update phone reputation
        phone_rep = PhoneReputation.query.filter_by(phone_number=phone).first()
        if phone_rep:
            phone_rep.report_count += 1
            phone_rep.reputation_score = risk_score
        else:
            phone_rep = PhoneReputation(
                phone_number=phone,
                report_count=1,
                reputation_score=risk_score
            )
            db.session.add(phone_rep)
        
        db.session.commit()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/voice', methods=['POST'])
def analyze_voice():
    """Analyze voice recording for scam indicators"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            # Analyze voice
            risk_score, reasons, details = get_voice_processor().analyze_voice(filepath)
            
            # Get transcription from details
            transcription = details.get('transcription', '')
            
            # Determine scam type
            if risk_score > 70:
                scam_type = "Suspicious Voice Call"
            elif risk_score > 40:
                scam_type = "Potentially Suspicious Call"
            else:
                 scam_type = "Legitimate Call"
            
            result = {
                "risk_score": round(risk_score, 1),
                "reasons": reasons,
                "transcription": transcription[:500],  # Return first 500 chars
                "scam_type": scam_type
            }
            
            # Save to database
            report = ReportedScam(
                scam_type=scam_type,
                description=transcription[:500],
                risk_score=risk_score,
                source_type="voice",
                file_path=filepath,
                analysis_details=json.dumps(result)
            )
            db.session.add(report)
            db.session.commit()
            
            return jsonify(result)
        
        finally:
            # Always cleanup the uploaded file
            cleanup_file(filepath)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chatbot():
    """AI Scam Assistant Chatbot"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Simple scam awareness responses
        message_lower = message.lower()
        
        responses = {
            "job": "Beware of fake job offers! Red flags include: requests for upfront fees, no interview process, unrealistic salaries. Always verify the company website directly.",
            "payment": "Never send money upfront for job offers, loans, or prizes. Legitimate companies never ask for advance payment.",
            "phishing": "Don't click suspicious links or provide personal info. Check sender email, hover over links before clicking, and verify with the official company directly.",
            "investment": "Be skeptical of 'guaranteed returns' claims. No investment is risk-free. Research the company and advisor credentials.",
            "lottery": "If you didn't enter a lottery, you didn't win. Scammers claim you won to get you to pay 'processing fees'.",
            "otp": "Never share your OTP (One-Time Password) with anyone, not even bank staff. They will never ask for it.",
            "verify": "Request from your bank to 'verify' info are usually scams. Call your bank directly using the number on their official website.",
         "password": "Legitimate companies never ask for your password. Change passwords immediately if compromised.",
            "crypto": "Cryptocurrency scams are rampant. Be extra cautious with crypto investment schemes."
        }
        
        # Generate response
        response_text = "I can help! What specific concern do you have? You can ask about job scams, phishing, investments, payments, lottery, OTP, verification, passwords, or cryptocurrency."
        
        for keyword, response in responses.items():
            if keyword in message_lower:
                response_text = response
                break
        
        return jsonify({
            "response": response_text,
            "message": message
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== REPORT MANAGEMENT ====================

@app.route('/api/report', methods=['POST'])
def submit_report():
    """Submit a scam report"""
    try:
        data = request.json
        
        report = ReportedScam(
            scam_type=data.get('scam_type', 'Unknown'),
            description=data.get('description', ''),
            risk_score=data.get('risk_score', 0),
            source_type=data.get('source_type', 'user_report'),
            email=data.get('email'),
            phone_number=data.get('phone'),
            url=data.get('url'),
            location=data.get('location'),
            analysis_details=json.dumps(data.get('details', {}))
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({"success": True, "report_id": report.id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Delete a specific scam report"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        report = ReportedScam.query.get(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404
        db.session.delete(report)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reports/all', methods=['DELETE'])
def delete_all_reports():
    """Delete all scam reports"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        ReportedScam.query.delete()
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/download-csv')
def download_reports_csv():
    """Download reports as CSV file"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    reports = ReportedScam.query.order_by(ReportedScam.created_at.desc()).all()
    
    # Generate CSV in memory
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Date', 'Email', 'Scam Type', 'Risk Score', 'Confidence', 'Description'])
    
    for r in reports:
        cw.writerow([
            r.id, 
            r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            r.email or 'N/A',
            r.scam_type,
            r.risk_score,
            r.confidence,
            r.description
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=scam_reports.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# ==================== KEYWORD MANAGEMENT ====================

@app.route('/api/admin/keywords', methods=['GET'])
def get_keywords():
    """Get all scam keywords"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        keywords = ScamKeyword.query.all()
        return jsonify({
            "keywords": [{"id": k.id, "keyword": k.keyword, "category": k.scam_category} for k in keywords]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/keywords', methods=['POST'])
def add_keyword():
    """Add a new scam keyword"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.json
        keyword_text = data.get('keyword', '').strip().lower()
        category = data.get('category', '')
        
        if not keyword_text:
            return jsonify({"error": "Keyword cannot be empty"}), 400
        
        existing = ScamKeyword.query.filter_by(keyword=keyword_text).first()
        if existing:
            return jsonify({"error": "Keyword already exists"}), 400
        
        new_kw = ScamKeyword(keyword=keyword_text, scam_category=category)
        db.session.add(new_kw)
        db.session.commit()
        
        return jsonify({"success": True, "id": new_kw.id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/keywords/<int:kw_id>', methods=['DELETE'])
def delete_keyword(kw_id):
    """Delete a scam keyword"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        keyword = ScamKeyword.query.get(kw_id)
        if not keyword:
            return jsonify({"error": "Keyword not found"}), 404
        
        db.session.delete(keyword)
        db.session.commit()
        
        return jsonify({"success": True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==================== ANALYTICS ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get platform statistics"""
    try:
        total_reports = ReportedScam.query.count()
        scam_by_type = db.session.query(ReportedScam.scam_type, db.func.count()).group_by(ReportedScam.scam_type).all()
        scam_by_source = db.session.query(ReportedScam.source_type, db.func.count()).group_by(ReportedScam.source_type).all()
        
        return jsonify({
            "total_reports": total_reports,
            "by_type": {scam_type: count for scam_type, count in scam_by_type},
            "by_source": {source_type: count for source_type, count in scam_by_source}
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/map-data', methods=['GET'])
def get_map_data():
    """Get scam location data for map visualization"""
    try:
        locations = ScamLocation.query.all()
        return jsonify({
            "locations": [{
                "city": loc.city,
                "country": loc.country,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "scam_type": loc.scam_type,
                "report_count": loc.report_count
            } for loc in locations]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

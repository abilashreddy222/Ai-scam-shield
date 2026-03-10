# AI Scam Shield – Universal Fraud Detection System

AI Scam Shield is an **AI-powered cybersecurity platform** designed to detect and prevent online scams.  
The system analyzes suspicious **text, emails, URLs, screenshots, and documents** using Artificial Intelligence and security intelligence techniques.

The goal of this project is to help users identify scams such as:

- Phishing emails  
- Fake job offers  
- Crypto fraud  
- Lottery scams  
- Malicious websites  

---

# Project Overview

Online scams are increasing rapidly. Many people fall victim to fake job offers, phishing emails, fraudulent investment schemes, and malicious websites.

AI Scam Shield acts as an **intelligent detection system** that analyzes suspicious content and generates a **Risk Score (0–100)** indicating whether the content is safe or dangerous.

The platform combines:

- Natural Language Processing (NLP)  
- Machine Learning  
- OCR (Optical Character Recognition)  
- Domain Intelligence  

to detect fraudulent activities.

---

# Features

AI Scam Shield can analyze multiple types of inputs:

- Text messages  
- Emails  
- Website URLs  
- Screenshots  
- PDF documents  
- Phone numbers  
- Voice messages  

Main capabilities include:

- AI-powered scam classification  
- Phishing URL detection  
- Screenshot and document OCR analysis  
- Chrome extension for real-time website scanning  
- Admin dashboard for monitoring threats  
- Dynamic risk scoring system  

---

# How the System Works

### Step 1 – User Input
The user submits suspicious content such as:

- Text  
- Email  
- URL  
- Screenshot  
- PDF  

### Step 2 – AI Processing
The system analyzes the content using AI models and cybersecurity intelligence.

### Step 3 – Risk Calculation
The system generates a **risk score between 0 and 100**.

### Step 4 – Result
The platform returns a result such as:

- SAFE  
- SUSPICIOUS  
- HIGH RISK SCAM  

---

# AI Text Analysis (NLP)

The system uses the **DistilBERT transformer model from HuggingFace** for Natural Language Processing.

The AI model can classify messages into categories such as:

- Fake Job Scam  
- Phishing Email  
- Investment Scam  
- Loan Scam  
- Lottery Scam  
- Cryptocurrency Scam  
- E-commerce Fraud  
- OTP Scam  
- Legitimate Content  

Unlike simple keyword systems, **BERT understands the context and meaning of sentences**.

---

# URL Phishing Detection

When a URL is analyzed, the system performs several cybersecurity checks:

- Domain age verification using WHOIS  
- Detection of suspicious domains such as `.tk`, `.xyz`, `.ml`  
- Typosquatting detection  
  - Example: `g00gle.com` instead of `google.com`  
- Suspicious URL structure detection  
- Security validation  

These signals are combined to generate a final **risk score**.

---

# OCR Image and Document Analysis

Scammers often hide malicious content inside **images or PDF documents**.

AI Scam Shield uses **Tesseract OCR** to extract text from:

- Screenshots  
- Posters  
- Scam messages  
- Fake job offer letters  
- PDF documents  

The extracted text is automatically analyzed by the AI engine.

---

# Chrome Extension

AI Scam Shield includes a **Google Chrome Extension** for real-time protection.

### Workflow

1. User clicks the extension icon  
2. The extension reads the current website URL  
3. The URL is sent to the backend API  
4. The phishing detection engine analyzes the domain  
5. A **risk indicator (Green / Yellow / Red)** appears instantly  

This allows users to detect suspicious websites without leaving the page.

---

# Admin Dashboard

The platform includes a secure **Admin Panel** for monitoring scam activity.

Admin features include:

- Viewing scam reports submitted by users  
- Managing suspicious keywords  
- Removing outdated rules  
- Exporting scam reports to CSV files  
- Monitoring scam trends  

### Default admin login

Username: `admin`  
Password: `admin123`

---

# Technology Stack

### Backend
- Python  
- Flask  
- SQLAlchemy  
- SQLite  

### Artificial Intelligence
- HuggingFace Transformers  
- DistilBERT  
- PyTorch  

### Security Intelligence
- python-whois  
- tldextract  

### Computer Vision
- OpenCV  
- Tesseract OCR  

### Frontend
- HTML  
- CSS  
- JavaScript  

### Browser Integration
- Chrome Extension (Manifest V3)

---

# Project Structure

```
Ai-scam-shield

app.py
database.py
requirements.txt

ai_engine/
templates/
static/
chrome_extension/
instance/
```

---

# Installation Guide

### Clone the repository

```
git clone https://github.com/abilashreddy222/Ai-scam-shield.git
```

### Navigate to the project folder

```
cd Ai-scam-shield
```

### Install dependencies

```
pip install -r requirements.txt
```

### Run the application

```
python app.py
```

### Open in browser

```
http://127.0.0.1:5000
```

---

# Real World Applications

AI Scam Shield can be used for:

- Phishing email detection  
- Fake job offer detection  
- Cryptocurrency fraud monitoring  
- Online marketplace scam detection  
- Enterprise cybersecurity monitoring systems  

---

# AI Assistance

This project was developed with the assistance of modern AI tools for:

- System architecture brainstorming  
- Debugging Python and Flask issues  
- Improving documentation  
- Optimizing machine learning workflows  

The final integration, testing, and system implementation were completed by the author.

---

# Contributing

Contributions are welcome.

If you would like to improve this project:

1. Fork the repository  
2. Create a new branch  
3. Make improvements or bug fixes  
4. Submit a pull request  

---

# License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this project as long as credit is given to the original author.

---

# Author

**Vanam Abilash Reddy**  
B.Tech Computer Science  
AI Enthusiast  

GitHub:  
https://github.com/abilashreddy222

---

# Acknowledgements

Special thanks to the open-source technologies used in this project:

- Python  
- Flask  
- HuggingFace Transformers  
- PyTorch  
- OpenCV  
- Tesseract OCR  

These technologies made it possible to build this AI-powered fraud detection platform.

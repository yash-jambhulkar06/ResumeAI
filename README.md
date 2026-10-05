# 🚀 ResumeAI

<p align="center">
  <strong>Analyze. Improve. Get Hired.</strong><br>
  <em>Next-generation AI resume evaluator, ATS compatibility scanner, and Google XYZ bullet point rewriter.</em>
</p>

<p align="center">
  <a href="https://resumeai-1-g53v.onrender.com">
    <img src="https://img.shields.io/badge/Live_Demo-Render-4f46e5?style=for-the-badge&logo=render&logoColor=white" alt="Live Demo" />
  </a>
  <img src="https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/Groq-Cloud_LLM-f55036?style=for-the-badge&logo=fastapi&logoColor=white" alt="Groq" />
  <img src="https://img.shields.io/badge/Docker-Production_Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License" />
</p>

---

## 🌐 Live Application

Explore the deployed application in production:  
👉 **[Open ResumeAI Live Demo](https://resumeai-1-g53v.onrender.com)**

---

## ✨ Features

- **🎯 Autonomous Profile & Seniority Detection**: Evaluates resumes on their own without requiring you to manually enter a job title. Incurs domain specialization and career level automatically.
- **📊 Dual Composite Scores**:
  - **Overall Resume Score (0–100)**: Holistic evaluation of clarity, achievements, and career depth.
  - **ATS Compatibility Score (0–100)**: Benchmark of how well legacy and modern Applicant Tracking Systems parse your content.
- **📈 4 Granular Category Breakdowns**:
  - *Impact & Quantifiable Metrics* (numbers, %, scale, and strong action verbs).
  - *ATS Parsability & Layout* (single-column readability, standard headers, parsable text).
  * *Technical Skills & Domain Depth* (modern frameworks, languages, and competencies).
  * *Structure, Brevity & Clarity* (bullet density, readability, and concise phrasing).
- **🤖 Deterministic ATS Compliance Checklist**: Automated checks for direct email & phone contacts, LinkedIn/GitHub profiles, standard section headers, metric frequency, and optimal word count.
- **✨ Google "XYZ" Bullet Point Rewriter**: Extracts weak bullet points and rewrites them using Google's executive hiring formula:  
  > *"Accomplished **[X]**, as measured by **[Y]**, by doing **[Z]**"*
- **📋 One-Click Copy**: 1-click clipboard buttons for suggestions and rewritten bullets with toast notifications.
- **📄 Multi-Format Resume Extraction**: Native in-memory text parsing for **PDF**, **DOCX** (including tables), **TXT**, and **OCR for images (JPG, PNG)** via Pillow and Tesseract.
- **⚡ Real-Time Animated Multi-Step Stepper**: Smooth, glassmorphism progress modal highlighting analysis steps in real time.
- **🖨️ Executive PDF Report Export**: Clean, print-optimized stylesheet (`@media print`) designed for clean 1-2 page exportable PDF report cards.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Django 6.1
- **LLM / AI Engine**: Groq Cloud API (`openai/gpt-oss-20b` / `llama-3.3-70b-versatile`) with constrained JSON mode & dynamic multi-model fallback
- **Document Parsing**: `pypdf`, `python-docx`, `pillow`, `pytesseract`
- **WSGI / Production Server**: Gunicorn (multi-worker with concurrency threads & 120s timeout)
- **Static Asset Serving**: WhiteNoise (`CompressedManifestStaticFilesStorage`)
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Containerization**: Docker (multi-stage, non-root user, built-in health probe)

---

## 🏗️ Architecture

```
ResumeAI/
├── analyzer/
│   ├── models.py            # ResumeAnalysis model with JSONField details & seniority
│   ├── views.py             # Thin controller coordinating services
│   ├── tests.py             # Full unit test suite (extraction, ATS checks, AI mocks)
│   ├── services/
│   │   ├── extractor.py     # PDF, DOCX, TXT, and OCR image text extraction
│   │   ├── ats_auditor.py   # Deterministic ATS regex scanner (contacts, metrics, sections)
│   │   └── ai_analyzer.py   # Groq API integration, JSON mode, & XYZ formula rewriter
│   └── templates/analyzer/
│       ├── home.html        # Upload & paste form with animated multi-step loader
│       └── result.html      # Executive audit report dashboard
├── config/                  # Django project settings, WSGI, URLs & /health/ probe
├── templates/               # Custom production 404.html and 500.html error pages
├── Dockerfile               # Hardened container definition with non-root security
├── build.sh                 # Zero-config automated build script for Render / PaaS
└── requirements.txt         # Pinned Python dependencies
```

---

## 🚀 Quickstart & Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/yash-jambhulkar06/ResumeAI.git
cd ResumeAI
```

### 2. Create and activate a virtual environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
DJANGO_SECRET_KEY=django-insecure-development-only-key-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SECURE_SSL_REDIRECT=False

# Get your free API key at https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

### 5. Run Migrations & Start Development Server
```bash
python manage.py migrate
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser.

---

## 🧪 Running Tests

Execute the comprehensive automated test suite:
```bash
python manage.py test
```

---

## 🐳 Docker Deployment

Run with Docker locally or in production:
```bash
# Build the Docker image
docker build -t resumeai:latest .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY="your_groq_api_key" \
  -e DJANGO_SECRET_KEY="your_secret_key" \
  resumeai:latest
```

---

## 🌐 Deploying to Render

1. Create a **New Web Service** connected to your repository on [Render](https://dashboard.render.com).
2. Select **Docker** as the environment (or Python with `./build.sh` build command).
3. Set **Health Check Path** to `/health/`.
4. In **Environment Variables**, add:
   ```env
   DJANGO_SECRET_KEY=your_secure_secret_key
   DEBUG=False
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=openai/gpt-oss-20b
   SECURE_SSL_REDIRECT=True
   SECURE_HSTS_SECONDS=31536000
   ```
5. Click **Deploy**!

---

## 🔒 Security & Reliability

- **Health Check Probe (`/health/`)**: Verifies database connectivity and service availability for uptime monitors and zero-downtime rolling deploys.
- **Privacy-First**: Resume text is evaluated in-memory and not stored in public storage buckets.
- **Container Hardening**: Docker runs under an unprivileged `appuser` user rather than `root`.
- **Production Defense**: Built-in HTTP Strict Transport Security (HSTS), Clickjacking defense (`X_FRAME_OPTIONS`), and MIME sniffing protection.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

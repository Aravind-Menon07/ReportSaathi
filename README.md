# ReportSaathi (रिपोर्ट साथी / ರಿಪೋರ್ಟ್ ಸಾಥಿ)

> **Empowering patients and caregivers with clear, plain-language explanations of medical lab reports and prescriptions.**

[![CI Pipeline](https://github.com/Aravind-Menon07/ReportSaathi/actions/workflows/ci.yml/badge.svg)](https://github.com/Aravind-Menon07/ReportSaathi/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Node.js: 20+](https://img.shields.io/badge/Node.js-20+-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![React: 18.3](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![FastAPI: 0.162](https://img.shields.io/badge/FastAPI-0.162-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Tests: 40 Passed](https://img.shields.io/badge/Tests-40%20Passed-brightgreen)](tests/)

---

## 1. Overview

**ReportSaathi** (*"Report Companion"*) is an educational health literacy tool designed to eliminate clinical jargon and bridge the communication gap between healthcare providers and patients in India.

When patients receive diagnostic test reports or printed prescriptions, they are routinely confronted with dense clinical terminology (*leukocytosis*, *creatinine*), unfamiliar laboratory units, and Latin shorthand (*BD*, *TDS*, *HS*). During rushed 5–10 minute consultations, patients often leave clinics without understanding their results, leading to search-engine panic or unsafe self-medication.

ReportSaathi converts uploaded medical reports (`PDF`, `JPG`, `PNG` up to 10 MB) into simple, accessible explanations in the patient's preferred language (**English**, **Hindi**, or **Kannada**), strictly verified against the normal reference ranges printed directly on their own document.

---

## 2. Critical Medical Safety & Regulatory Non-Negotiables (`docs/06b-safety-rules.md`)

1. **ZERO DIAGNOSIS:** Never diagnose illnesses, predict diseases, or claim a patient is disease-free.
2. **ZERO MEDICATION MODIFICATION:** Never advise starting, stopping, increasing, or decreasing prescription medicine dosages.
3. **STRICT REPORT REFERENCE RANGES:** Compare laboratory values **ONLY** against ranges printed on the report. If a value lacks a printed range, assign `no_range_on_report` (NEVER assume standard population ranges).
4. **DETERMINISTIC RED FLAGS BEFORE AI:** Emergency alerts for critical Potassium, Platelets, Hemoglobin, Glucose, and Creatinine **MUST** execute programmatically in pure Python **BEFORE** any AI explanation generation.
5. **MANDATORY DISCLAIMER:** Every screen, PDF, and API payload displays:  
   > *"This explains your report. It does not replace your doctor."*
6. **EPHEMERAL PROCESSING & 10 MB LIMIT:** Maximum upload size is 10 MB. Temporary files and extracted text are securely wiped after processing with zero permanent storage in compliance with the **Digital Personal Data Protection (DPDP) Act, 2023**.

---

## 3. Project File Tree

```text
ReportSaathi/
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI workflow (40 Python tests + Vite build)
├── backend/
│   ├── __init__.py
│   ├── main.py                        # FastAPI application with REST endpoints & CORS
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── rules.py                   # Deterministic 5% range evaluator & critical red flags
│   │   ├── banned_phrases.py          # Prohibited assertion detector & AI sanitizer
│   │   └── privacy.py                 # PrivacyPreservingLogFilter & EphemeralStorageManager
│   └── integrations/
│       ├── __init__.py
│       └── ocr.py                     # Tesseract OCR, noise scoring, regex parser, user corrections
├── shared/
│   ├── types.ts                       # Shared TypeScript contracts
│   └── sample-report.json             # Gold-standard adult CBC fixture
├── frontend/
│   ├── index.html                     # HTML5 entry point
│   ├── package.json                   # React 18, Vite 5, Lucide icons
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── tsconfig.node.json
│   ├── vite.config.ts                 # Vite server & API proxy
│   └── src/
│       ├── main.tsx                   # React root mount
│       ├── App.tsx                    # Multi-screen application router & state manager
│       ├── index.css                  # Tailwind styles & print CSS
│       ├── types.ts                   # Frontend TypeScript interfaces
│       ├── api.ts                     # API client with health probe & zero mock fallbacks
│       └── components/
│           ├── Header.tsx             # App header with language/level badges & reset
│           ├── Footer.tsx             # Fixed footer with mandatory medical disclaimer
│           ├── LanguageSelector.tsx   # English, Hindi, Kannada & Simple, Standard, Detailed
│           ├── UploadView.tsx         # Drag-and-drop, 10MB limit, sample loader, DPDP consent
│           ├── CheckValuesView.tsx    # HITL editable verification table & empty-state warning
│           ├── ResultsView.tsx        # Red-flag emergency banner & explained biomarker cards
│           ├── DoctorQuestionsView.tsx# 3 to 6 targeted doctor consultation questions
│           └── ShareView.tsx          # WhatsApp summary share & printable PDF export
├── tests/
│   ├── test_safety.py                 # 13 tests: range boundaries, missing ranges, red flags
│   ├── test_ocr.py                    # 5 tests: extraction, blurry scans, Indian numbers, HITL
│   ├── test_api_contract.py           # 13 tests: endpoint schemas, 10MB limit, HTTP codes
│   ├── test_privacy.py                # 9 tests: PHI log scrubbing, path traversal, TTL wipe
│   └── fixtures/
│       ├── 01-normal-report.json      # Standard normal CBC
│       ├── 02-high-values.json        # Elevated cholesterol
│       ├── 03-low-values.json         # Low Hb + prescription
│       ├── 04-missing-ranges.json     # CRP with missing range
│       ├── 05-blurry-report.json      # Garbled low-light scan
│       ├── 06-multiple-values.json    # 14-parameter multi-panel
│       ├── 07-scanned-pdf.json        # Metropolis tabular scan
│       ├── 07-scanned-pdf.txt         # Multi-column text
│       ├── 08-ocr-challenges.json     # 3,25,000 /cumm and < 0.5 operators
│       ├── 09-multilingual-report.json# Trilingual translations
│       └── 10-red-flag-case.json      # Emergency critical red-flag values
├── docs/
│   ├── 01.problem.md                  # Stage 1: Problem Definition
│   ├── 02.research.md                 # Stage 2: Empirical Research & Regulatory Requirements
│   ├── 03.scope.md                    # Stage 3: Scope Definition & Boundaries
│   └── 04.architecture.md             # Stage 4: System Architecture & Technical Specifications
└── README.md
```

---

## 4. Running the 40-Test QA Suite

The test suite requires zero external network dependencies and executes against Python's built-in `unittest` runner:

```powershell
python -m unittest discover tests -v
```

### Test Suite Breakdown (100% Passing)

| Test File | Test Count | Scope Verified |
| :--- | :--- | :--- |
| `tests/test_safety.py` | 13 | Normal, borderline (within 5%), out-of-range, missing range discipline (`no_range_on_report`), Potassium, Platelet, Hemoglobin, Glucose, Creatinine red flags, and banned phrase regex neutralization. |
| `tests/test_ocr.py` | 5 | Clean OCR text extraction, noise ratio clarity scoring (> 0.15), missing range parser, Indian comma number formatting (`3,25,000`), and user correction re-validation. |
| `tests/test_api_contract.py` | 13 | Schema validation, 10 MB payload limit (413), empty file rejection (400), unsupported format (415), empty correction rejection (422), mandatory disclaimer presence, and feedback rating bounds. |
| `tests/test_privacy.py` | 9 | Phone numbers, Aadhaar IDs, emails, numerical lab values, drug names log scrubbing, logging filter integration, path traversal defense (`../`), null-byte defense (`\0`), on-demand wipe (TC-26), and TTL purge. |
| **Total** | **40** | **40 / 40 Passed (100%)** |

---

## 5. Development & Execution Guide

### Start FastAPI Backend

```powershell
uvicorn backend.main:app --reload --port 8000
```
* Interactive API Documentation (Swagger): `http://localhost:8000/docs`
* Health Check: `http://localhost:8000/api/health`

### Build & Run Frontend

```powershell
cd frontend
npm install
npm run build
npm run dev
```
* Frontend Application: `http://localhost:5173`

---

## 6. Regulatory & Privacy Notice

ReportSaathi complies with the **Digital Personal Data Protection (DPDP) Act, 2023** (India). Uploaded documents and extracted strings are retained solely in ephemeral server RAM during extraction and explanation generation, after which they are permanently wiped. No Protected Health Information (PHI) is persisted or used for AI model training.

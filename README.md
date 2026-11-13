# ReportSaathi (रिपोर्ट साथी / ರಿಪೋರ್ಟ್ ಸಾಥಿ)

> **Empowering patients and caregivers with clear, plain-language explanations of medical lab reports and prescriptions.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Node.js: 20+](https://img.shields.io/badge/Node.js-20+-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![Tesseract OCR: 5.x](https://img.shields.io/badge/Tesseract_OCR-5.x-5C5C5C)](https://github.com/tesseract-ocr/tesseract)
[![Powered by Gemini](https://img.shields.io/badge/AI-Google_Gemini-4285F4?logo=google&logoColor=white)](https://aistudio.google.com)

---

## 1. Overview

**ReportSaathi** (*"Report Companion"*) is a patient-first health communication tool designed to eliminate medical jargon and bridge the communication gap between healthcare providers and patients in India.

When patients receive diagnostic test reports, lab panels, or printed prescriptions, they are routinely confronted with dense clinical terminology (*leukocytosis*, *creatinine*), unfamiliar laboratory units, and Latin shorthand (*BD*, *TDS*, *HS*). During rushed 5–10 minute consultations, patients often leave clinics without understanding their results, leading to search-engine panic or unsafe self-medication.

ReportSaathi converts uploaded medical reports (`PDF`, `JPG`, `PNG`) into simple, accessible explanations in the patient's preferred language (**English**, **Hindi**, or **Kannada**), strictly verified against the normal reference ranges printed directly on their own document.

---

## 2. Core Pillars & Safety Guardrails

| Pillar | What ReportSaathi Does | Hard Safety Boundary (What It NEVER Does) |
| :--- | :--- | :--- |
| **Document-Grounded** | Compares extracted test values **strictly** against the reference ranges printed on the user's specific lab slip. | **Never Invents Ranges:** Never substitutes or infers missing ranges from external textbooks or databases. |
| **No-Diagnosis Policy** | Explains what biomarkers measure in simple everyday terms (e.g., *"Hemoglobin carries oxygen in your blood"*). | **Never Diagnoses:** Never names suspected diseases, conditions, or ranks diagnostic likelihoods. |
| **Prescription Clarity** | Translates frequency abbreviations (*OD* = once daily, *BD* = twice daily with food) into plain language while preserving the exact prescribed drug name and dose verbatim. | **Never Recommends Treatments:** Never alters dosages, suggests alternative drugs, or advises starting/stopping medications. |
| **Red-Flag Escalation** | Flags critically abnormal biomarker thresholds with urgent, prominent visual banners directing immediate clinical attention. | **Never Triages Emergencies:** Clearly states it is not an emergency triage or clinical decision-support system. |
| **Consultation Readiness** | Generates 3–5 personalized, non-directive questions the patient can carry into their next doctor visit. | **Never Replaces Doctors:** Re-iterates on every screen and PDF summary that explanations are educational. |
| **Ephemeral Privacy** | Operates with zero permanent storage of Protected Health Information (PHI) and immediate memory purging in compliance with the Indian **DPDP Act (2023)**. | **No Third-Party Model Training:** Uses enterprise/developer zero-retention pipelines to ensure health data is never retained or trained on. |

---

## 3. Workshop & Project Stages

This repository follows the structured **Idea to Deployment** methodology:

* **Stage 1 — Problem Definition:** [`docs/01.problem.md`](docs/01.problem.md)  
  *Detailed examination of patient comprehension deficits, consultation time constraints, and risks of self-medication.*
* **Stage 2 — Research & Evidence:** [`docs/02.research.md`](docs/02.research.md)  
  *Quantitative health literacy data in India, competitive product landscape, complaint patterns, and Indian regulatory requirements (DPDP Act 2023).*
* **Stage 3 — Scope Definition:** [`docs/03.scope.md`](docs/03.scope.md)  
  *Core user journey, MVP boundaries, testable acceptance criteria, and explicit non-goals.*
* **Stage 4 — System Architecture:** [`docs/04.architecture.md`](docs/04.architecture.md)  
  *Component architecture, OCR processing pipeline, deterministic range comparison engine, prompt engineering templates, and privacy purge mechanics.*

---

## 4. Technical Architecture & Stack

```
+------------------------------------------------------------------------+
|                      Client Layer (Cloudflare Pages)                   |
|   Responsive React / Vite / Tailwind UI with Multilingual Support      |
|   (English, Hindi, Kannada) + DPDP Notice & Consent Gate               |
+-----------------------------------+------------------------------------+
                                    | HTTPS / Ephemeral Upload (Max 10MB)
                                    v
+------------------------------------------------------------------------+
|                        Backend Layer (Render)                          |
|                     FastAPI / Python 3.11+ Service                     |
+-----------------------------------+------------------------------------+
                                    |
      +-----------------------------+-----------------------------+
      v                                                           v
+-----------------------------------+   +------------------------------------+
|         OCR Pipeline              |   |     Deterministic Range Engine     |
|   - OpenCV image preprocessing    |   |   - Compares parsed values against |
|   - Tesseract OCR 5.x extraction  |   |     printed laboratory ranges      |
|   - Human-in-the-loop review UI   |   |   - Low / Normal / High / Critical |
+-----------------------------------+   +------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                      AI Explainer & Doctor Questions                   |
|   Google Gemini API with zero-retention controls                       |
|   - Plain-language simplification (Simple, Standard, Detailed)         |
|   - 3-5 structured, non-directive questions for the physician          |
|   - Strict system prompt guardrails against diagnosis & prescription   |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                          Output Generation                             |
|   - Interactive web review screen with side-by-side verification       |
|   - Client-side downloadable summary PDF (report, ranges, questions)   |
|   - Memory wipe & ephemeral session destruction                        |
+------------------------------------------------------------------------+
```

---

## 5. Development Setup & Verification

### Prerequisites

| Tool | Version Requirement | Purpose |
| :--- | :--- | :--- |
| **Git** | 2.x or newer | Version control and collaboration |
| **Node.js** | v20 LTS or higher | Frontend build system & Gemini CLI runner |
| **npm** | Compatible with Node | Package manager |
| **Python** | 3.11 or higher | Backend OCR pipeline & API services |
| **Tesseract OCR** | 5.x | Optical Character Recognition for printed reports |
| **Gemini CLI** | `@google/gemini-cli` | Terminal AI assistance and testing |
| **Antigravity IDE** | Latest | AI-assisted development environment |

### Verification Command

To verify that your local development environment meets all prerequisites:

```powershell
git --version; node --version; npm --version; python --version; pip --version; tesseract --version; gemini --version
```

**Expected terminal output:**
```text
git version 2.x
v20.x.x (or higher)
10.x.x
Python 3.11.x (or higher)
pip 24.x / 25.x
tesseract v5.x
0.x.x (Gemini CLI)
```

---

## 6. Repository Layout

```text
ReportSaathi/
├── assets/
│   └── saathi.png           # Project visual assets & branding
├── docs/
│   ├── 01.problem.md        # Stage 1: Problem Definition
│   ├── 02.research.md       # Stage 2: Research & Empirical Evidence
│   ├── 03.scope.md          # Stage 3: Project Scope & Guardrails
│   └── 04.architecture.md   # Stage 4: Technical Architecture
├── backend/                 # FastAPI backend (to be populated)
├── frontend/                # React / Vite frontend (to be populated)
└── README.md                # Project documentation & setup
```

---

## 7. Disclaimer

> **Medical & Regulatory Notice:**  
> ReportSaathi is an educational health literacy tool designed solely to assist patients in understanding their medical documents. It is **not** a medical device, diagnostic system, or clinical decision-support tool. It does **not** provide medical advice, diagnosis, or treatment. Users are explicitly advised to consult a qualified healthcare professional regarding any medical condition or laboratory finding.

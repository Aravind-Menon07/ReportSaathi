"""ReportSaathi Production-Grade FastAPI Backend Application.
Adheres strictly to docs/06b-safety-rules.md and docs/06c-api-contracts.md.
"""
import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from backend.safety.rules import evaluate_biomarker, check_red_flags
from backend.safety.banned_phrases import sanitize_ai_output, contains_banned_phrases, APPROVED_SAFETY_DISCLAIMER
from backend.safety.privacy import PrivacyPreservingLogFilter, EphemeralStorageManager
from backend.integrations.ocr import (
    run_tesseract,
    assess_text_clarity,
    parse_biomarkers_from_text,
    apply_user_corrections,
)

# Configure logger with privacy scrubbing filter
logger = logging.getLogger("reportsaathi")
logger.setLevel(logging.INFO)
privacy_filter = PrivacyPreservingLogFilter()
logger.addFilter(privacy_filter)

# Initialize FastAPI App
app = FastAPI(
    title="ReportSaathi API",
    description="Educational, plain-language medical report and prescription explainer backend.",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ephemeral storage manager (10 MB upload limit enforcement)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
storage_manager = EphemeralStorageManager()


# --- Pydantic Schemas ---

class BiomarkerItem(BaseModel):
    name: str
    value: Union[float, int, str]
    unit: Optional[str] = ""
    printed_range_low: Optional[float] = None
    printed_range_high: Optional[float] = None
    raw_range: Optional[str] = ""
    status: Optional[str] = "normal"
    explanation: Optional[str] = None


class MedicineItem(BaseModel):
    name: str
    dosage: Optional[str] = ""
    frequency: Optional[str] = ""
    timing: Optional[str] = ""
    instructions: Optional[str] = ""
    plain_explanation: Optional[str] = None


class RedFlagAlertItem(BaseModel):
    biomarker: str
    value: Union[float, int, str]
    severity: str = "critical"
    action_prompt: str
    message: str


class ExtractionRequest(BaseModel):
    document_id: str
    raw_text: Optional[str] = None


class CorrectionRequest(BaseModel):
    corrected_text: str

    @field_validator("corrected_text")
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Corrected text payload cannot be empty.")
        return v.strip()


class ExplainRequest(BaseModel):
    document_id: str
    biomarkers: List[BiomarkerItem] = []
    medicines: List[MedicineItem] = []
    language: str = "English"
    reading_level: str = "Standard"

    @field_validator("language")
    def validate_language(cls, v: str) -> str:
        allowed = {"English", "Hindi", "Kannada"}
        if v not in allowed:
            raise ValueError(f"Language must be one of {allowed}")
        return v

    @field_validator("reading_level")
    def validate_reading_level(cls, v: str) -> str:
        allowed = {"Simple", "Standard", "Detailed"}
        if v not in allowed:
            raise ValueError(f"Reading level must be one of {allowed}")
        return v


class QuestionsRequest(BaseModel):
    biomarkers: List[BiomarkerItem] = []
    language: str = "English"


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = ""
    document_id: Optional[str] = None


# --- Multilingual Explanation Templates ---

EXPLANATIONS_DB = {
    "hemoglobin": {
        "English": {
            "Simple": "Hemoglobin carries oxygen in your red blood cells. Think of it like delivery trucks carrying air to your body.",
            "Standard": "Hemoglobin is the oxygen-carrying protein in red blood cells. It ensures all muscles and tissues receive fresh oxygen from your lungs.",
            "Detailed": "Hemoglobin is an iron-rich metalloprotein in erythrocytes responsible for oxygen transport from alveolar capillaries to systemic tissues. Levels outside printed reference ranges warrant physician review.",
        },
        "Hindi": {
            "Simple": "हीमोग्लोबिन आपके रक्त में ऑक्सीजन पहुंचाने वाला प्रोटीन है। यह शरीर के सभी अंगों तक हवा पहुंचाता है।",
            "Standard": "हीमोग्लोबिन लाल रक्त कोशिकाओं में पाया जाने वाला महत्वपूर्ण प्रोटीन है जो फेफड़ों से पूरे शरीर में ऑक्सीजन पहुंचाता है।",
            "Detailed": "हीमोग्लोबिन एक आयरन युक्त प्रोटीन है जो एरिथ्रोसाइट्स में ऑक्सीजन परिवहन के लिए आवश्यक है। रिपोर्ट पर दी गई सामान्य सीमा से बाहर होने पर डॉक्टर से परामर्श करें।",
        },
        "Kannada": {
            "Simple": "ಹಿಮೋಗ್ಲೋಬಿನ್ ನಿಮ್ಮ ರಕ್ತದಲ್ಲಿ ಆಮ್ಲಜನಕವನ್ನು ಸಾಗಿಸುವ ಪ್ರೋಟೀನ್ ಆಗಿದೆ.",
            "Standard": "ಹಿಮೋಗ್ಲೋಬಿನ್ ಕೆಂಪು ರಕ್ತ ಕಣಗಳಲ್ಲಿರುವ ಪ್ರಮುಖ ಪ್ರೋಟೀನ್ ಆಗಿದ್ದು, ಶ್ವಾಸಕೋಶದಿಂದ ಇಡೀ ದೇಹಕ್ಕೆ ಆಮ್ಲಜನಕವನ್ನು ಪೂರೈಸುತ್ತದೆ.",
            "Detailed": "ಹಿಮೋಗ್ಲೋಬಿನ್ ಕೆಂಪು ರಕ್ತ ಕಣಗಳಲ್ಲಿ ಆಮ್ಲಜನಕ ಸಾಗಣೆಗೆ ಜವಾಬ್ದಾರಿಯುತ ಪ್ರೋಟೀನ್ ಆಗಿದೆ. ವರದಿಯಲ್ಲಿ ಮುದ್ರಿಸಲಾದ ಸಾಮಾನ್ಯ ಮಿತಿಗಿಂತ ವ್ಯತ್ಯಾಸವಿದ್ದರೆ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        },
    },
    "wbc": {
        "English": {
            "Simple": "White blood cells defend your body against infections like an internal security team.",
            "Standard": "White blood cells are an essential part of your immune system, fighting bacteria and viruses.",
            "Detailed": "Leukocytes constitute the cellular arm of the immune system, defending host tissue against pathogens and foreign antigens.",
        },
        "Hindi": {
            "Simple": "सफेद रक्त कोशिकाएं (WBC) संक्रमण और बीमारियों से लड़ने में मदद करती हैं।",
            "Standard": "श्वेत रक्त कोशिकाएं शरीर की रोग प्रतिरोधक क्षमता का मुख्य हिस्सा हैं जो संक्रमण से लड़ती हैं।",
            "Detailed": "ल्यूकोไซต์ಗಳು ರೋಗಕಾರಕಗಳ ವಿರುದ್ಧ ಹೋರಾಡುವ ರಕ್ಷಣಾ ವ್ಯವಸ್ಥೆಯಾಗಿವೆ.",
        },
        "Kannada": {
            "Simple": "ಬಿಳಿ ರಕ್ತ ಕಣಗಳು ಸೋಂಕುಗಳ ವಿರುದ್ಧ ಹೋರಾಡುವ ರಕ್ಷಣಾ ಕಣಗಳಾಗಿವೆ.",
            "Standard": "ಬಿಳಿ ರಕ್ತ ಕಣಗಳು ನಿಮ್ಮ ರೋಗನಿರೋಧಕ ಶಕ್ತಿಯ ಭಾಗವಾಗಿದ್ದು ಸೋಂಕುಗಳನ್ನು ತಡೆಯುತ್ತವೆ.",
            "Detailed": "ಲ್ಯುಕೋಸೈಟ್‌ಗಳು ರೋಗಕಾರಕಗಳ ವಿರುದ್ಧ ಹೋರಾಡುವ ಪ್ರತಿರಕ್ಷಣಾ ವ್ಯವಸ್ಥೆಯ ಮುಖ್ಯ ಕಣಗಳಾಗಿವೆ.",
        },
    },
    "platelets": {
        "English": {
            "Simple": "Platelets are cell fragments that plug cuts and help your blood clot normally.",
            "Standard": "Platelets are essential blood cells that clump together to stop bleeding when you have an injury.",
            "Detailed": "Thrombocytes play a central role in hemostasis, adhering to vascular endothelial lesions to form primary hemostatic plugs.",
        },
        "Hindi": {
            "Simple": "प्लेटलेट्स खून को जमने में मदद करते हैं ताकि चोट लगने पर खून बहना रुक सके।",
            "Standard": "प्लेटलेट्स रक्त के थक्के बनाने के लिए आवश्यक घटक हैं जो रक्तस्राव को रोकते हैं।",
            "Detailed": "थ्रोम्बोसाइट्स रक्त के थक्के जमने और हेमोस्टेसिस के लिए महत्वपूर्ण घटक हैं।",
        },
        "Kannada": {
            "Simple": "ಪ್ಲೇಟ್‌ಲೆಟ್‌ಗಳು ರಕ್ತ ಹೆಪ್ಪುಗಟ್ಟಲು ಮತ್ತು ರಕ್ತಸ್ರಾವ ನಿಲ್ಲಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತವೆ.",
            "Standard": "ಪ್ಲೇಟ್‌ಲೆಟ್‌ಗಳು ರಕ್ತ ಹೆಪ್ಪುಗಟ್ಟುವ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ಪ್ರಮುಖ ಪಾತ್ರ ವಹಿಸುತ್ತವೆ.",
            "Detailed": "ಥ್ರೊಂಬೊಸೈಟ್‌ಗಳು ಹೆಮೋಸ್ಟಾಸಿಸ್ ಮತ್ತು ರಕ್ತ ಹೆಪ್ಪುಗಟ್ಟುವಿಕೆಯಲ್ಲಿ ಪ್ರಮುಖವಾಗಿವೆ.",
        },
    },
    "cholesterol": {
        "English": {
            "Simple": "Cholesterol is a natural fat in your blood needed for cell building.",
            "Standard": "Cholesterol is a waxy lipid needed for hormone synthesis and cell membranes. High levels require dietary review.",
            "Detailed": "Serum total cholesterol reflects circulating esterified and free sterols across LDL, HDL, and VLDL fractions.",
        },
        "Hindi": {
            "Simple": "कोलेस्ट्रॉल रक्त में पाया जाने वाला वसा है जो शरीर की कोशिकाओं के लिए आवश्यक है।",
            "Standard": "कोलेस्ट्रॉल शरीर के लिए आवश्यक वसा है, लेकिन अधिक मात्रा होने पर हृदय स्वास्थ्य पर ध्यान देना चाहिए।",
            "Detailed": "सीरम कोलेस्ट्रॉल रक्त परिसंचರಣ में लिपिड सांद्रता को दर्शाता है।",
        },
        "Kannada": {
            "Simple": "ಕೊಲೆಸ್ಟ್ರಾಲ್ ರಕ್ತದಲ್ಲಿರುವ ಅಗತ್ಯ ಕೊಬ್ಬಿನಂಶವಾಗಿದೆ.",
            "Standard": "ಕೊಲೆಸ್ಟ್ರಾಲ್ ಜೀವಕೋಶಗಳ ಬೆಳವಣಿಗೆಗೆ ಅಗತ್ಯವಿರುವ ಜಿಡ್ಡಿನ ಪದಾರ್ಥವಾಗಿದೆ.",
            "Detailed": "ರಕ್ತದಲ್ಲಿನ ಕೊಲೆಸ್ಟ್ರಾಲ್ ಲಿಪಿಡ್ ಪ್ರೊಫೈಲ್‌ನ ಮುಖ್ಯ ಭಾಗವಾಗಿದೆ.",
        },
    },
}


# --- API Routes ---

@app.get("/api/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ReportSaathi API"}


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Uploads document with 10MB limit enforcement, format validation, and ephemeral ID creation."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload payload.",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{ext}'. Allowed formats are PDF, JPG, JPEG, and PNG.",
        )

    # Read content to check file size and empty file
    contents = await file.read()
    file_size = len(contents)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded. Please upload a valid medical report.",
        )

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 10 MB ({file_size} bytes received).",
        )

    doc_id = str(uuid.uuid4())
    doc_dir = storage_manager.create_document_dir(doc_id)
    save_path = doc_dir / f"document{ext}"
    save_path.write_bytes(contents)

    logger.info(f"Ephemeral document created: id={doc_id}, size={file_size}")

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "size_bytes": file_size,
        "status": "uploaded",
    }


@app.post("/api/extract")
def extract_text(payload: ExtractionRequest) -> Dict[str, Any]:
    """Extracts text, assesses clarity, and identifies initial biomarkers."""
    doc_id = payload.document_id
    raw_text = payload.raw_text or ""

    if not raw_text:
        doc_dir = storage_manager.get_document_dir(doc_id)
        if doc_dir:
            # Check for saved file
            for f in doc_dir.iterdir():
                if f.is_file() and not f.name.startswith("."):
                    if f.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                        raw_text = run_tesseract(f)
                    elif f.suffix.lower() == ".txt":
                        raw_text = f.read_text(encoding="utf-8", errors="replace")
                    break

    clarity = assess_text_clarity(raw_text)
    biomarkers = parse_biomarkers_from_text(raw_text)
    red_flags = check_red_flags(biomarkers)

    return {
        "document_id": doc_id,
        "status": clarity["status"],
        "requires_verification": clarity["requires_verification"],
        "clarity": clarity,
        "raw_text": raw_text,
        "biomarkers": biomarkers,
        "red_flags": red_flags,
    }


@app.post("/api/extract/{document_id}/corrections")
def submit_corrections(document_id: str, payload: CorrectionRequest) -> Dict[str, Any]:
    """Applies user-edited text corrections, re-parses biomarkers, and validates red-flags."""
    try:
        result = apply_user_corrections(payload.corrected_text)
        result["document_id"] = document_id
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@app.post("/api/explain")
def generate_explanations(payload: ExplainRequest) -> Dict[str, Any]:
    """Generates plain-language medical explanations strictly referencing printed ranges.
    Guarantees deterministic red-flag alert evaluation BEFORE explanation generation.
    """
    # 1. DETERMINISTIC RED FLAGS BEFORE AI (Non-negotiable)
    red_flags = check_red_flags(payload.biomarkers)

    lang = payload.language
    level = payload.reading_level
    disclaimer = "This explains your report. It does not replace your doctor."

    explained_biomarkers = []
    for b in payload.biomarkers:
        b_dict = b.model_dump()
        name_lower = b.name.lower()

        # Find matching explanation template or generate safe default
        matched_key = None
        for k in EXPLANATIONS_DB:
            if k in name_lower:
                matched_key = k
                break

        if matched_key and lang in EXPLANATIONS_DB[matched_key]:
            base_exp = EXPLANATIONS_DB[matched_key][lang].get(level, EXPLANATIONS_DB[matched_key][lang]["Standard"])
        else:
            base_exp = f"{b.name} measures an important physiological indicator in your laboratory test."

        # Re-evaluate status strictly against printed ranges
        computed_status = evaluate_biomarker(
            b.name, b.value, b.unit, b.printed_range_low, b.printed_range_high
        )
        b_dict["status"] = computed_status

        if computed_status == "no_range_on_report":
            range_note = " No normal reference range was printed on your document for this test."
        elif computed_status == "normal":
            range_note = f" Your value of {b.value} is within the printed reference range ({b.raw_range})."
        elif computed_status == "borderline":
            range_note = f" Your value of {b.value} is close to the boundary of the printed reference range ({b.raw_range})."
        else:
            range_note = f" Your value of {b.value} is outside the printed reference range ({b.raw_range})."

        full_exp = base_exp + range_note
        # Run banned phrase sanitizer
        sanitized_exp = sanitize_ai_output(full_exp)
        b_dict["explanation"] = sanitized_exp
        explained_biomarkers.append(b_dict)

    # Generate 3 to 6 targeted doctor questions
    questions = _generate_questions(payload.biomarkers, lang)

    # Construct overall educational summary
    summary_text = (
        f"This summary explains your report in {lang} at the {level} reading level. "
        f"A total of {len(explained_biomarkers)} test parameters were reviewed against the reference ranges printed on your document."
    )
    if red_flags:
        summary_text += " ATTENTION: Critical values were detected that require immediate medical consultation."

    return {
        "document_id": payload.document_id,
        "status": "ready",
        "requires_verification": False,
        "disclaimer": disclaimer,
        "language": lang,
        "reading_level": level,
        "summary": sanitize_ai_output(summary_text),
        "biomarkers": explained_biomarkers,
        "medicines": [m.model_dump() for m in payload.medicines],
        "red_flags": red_flags,
        "doctor_questions": questions,
    }


@app.post("/api/questions")
def get_doctor_questions(payload: QuestionsRequest) -> Dict[str, Any]:
    """Returns 3 to 6 targeted doctor questions based on out-of-range or abnormal results."""
    questions = _generate_questions(payload.biomarkers, payload.language)
    return {
        "doctor_questions": questions,
        "disclaimer": "This explains your report. It does not replace your doctor.",
    }


@app.post("/api/feedback")
def submit_feedback(payload: FeedbackRequest) -> Dict[str, Any]:
    """Records patient feedback."""
    return {
        "status": "received",
        "rating": payload.rating,
        "message": "Thank you for your feedback. ReportSaathi is continuously improving.",
    }


@app.delete("/api/document/{document_id}")
def delete_document(document_id: str) -> Dict[str, Any]:
    """On-demand deletion of temporary document files for zero-retention compliance."""
    success = storage_manager.cleanup_document(document_id)
    return {
        "document_id": document_id,
        "deleted": success,
        "status": "purged",
    }


def _generate_questions(biomarkers: List[Any], language: str = "English") -> List[str]:
    """Generates 3 to 6 relevant, non-directive questions for the physician."""
    questions: List[str] = []
    abnormal_names = []

    for b in biomarkers:
        b_dict = b.model_dump() if hasattr(b, "model_dump") else (b if isinstance(b, dict) else {})
        status = b_dict.get("status")
        name = b_dict.get("name", "")
        if status in {"needs_attention", "borderline"}:
            abnormal_names.append(name)

    if language == "Hindi":
        if abnormal_names:
            first = abnormal_names[0]
            questions.append(f"मेरी रिपोर्ट में {first} सामान्य सीमा से बाहर क्यों है?")
        questions.append("क्या इन परिणामों के आधार पर मुझे कोई आहार या जीवनशैली में बदलाव करने की आवश्यकता है?")
        questions.append("मुझे यह परीक्षण दोबारा कब करवाना चाहिए?")
        questions.append("क्या इन परिणामों के लिए मुझे किसी अन्य विशेषज्ञ डॉक्टर से मिलने की आवश्यकता है?")
    elif language == "Kannada":
        if abnormal_names:
            first = abnormal_names[0]
            questions.append(f"ನನ್ನ ವರದಿಯಲ್ಲಿ {first} ಸಾಮಾನ್ಯ ಮಿತಿಗಿಂತ ಏಕೆ ಭಿನ್ನವಾಗಿದೆ?")
        questions.append("ಈ ಫಲಿತಾಂಶಗಳ ಆಧಾರದ ಮೇಲೆ ನಾನು ಯಾವುದೇ ಆಹಾರ ಅಥವಾ ಜೀವನಶೈಲಿಯಲ್ಲಿ ಬದಲಾವಣೆ ಮಾಡಬೇಕೇ?")
        questions.append("ನಾನು ಈ ಪರೀಕ್ಷೆಯನ್ನು ಯಾವಾಗ ಪುನರಾವರ್ತಿಸಬೇಕು?")
        questions.append("ಈ ಫಲಿತಾಂಶಗಳಿಗಾಗಿ ನಾನು ತಜ್ಞ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಬೇಕೇ?")
    else:
        if abnormal_names:
            first = abnormal_names[0]
            questions.append(f"What factors might be contributing to my {first} being outside the printed normal range?")
        questions.append("Do any of these results suggest that I should modify my diet, hydration, or daily activities?")
        questions.append("When should I schedule a follow-up test to recheck these specific parameters?")
        questions.append("Are there any additional diagnostic investigations or screenings you recommend based on this report?")

    # Ensure between 3 and 6 questions
    return questions[:6]


/**
 * ReportSaathi Shared TypeScript Contracts
 * Core definitions for clinical status, biomarkers, alerts, medicines, and report payloads.
 */

export type ClinicalStatus = 'normal' | 'borderline' | 'needs_attention' | 'no_range_on_report';

export type ReadingLevel = 'Simple' | 'Standard' | 'Detailed';
export type SupportedLanguage = 'English' | 'Hindi' | 'Kannada';

export interface BiomarkerValue {
  name: string;
  value: number | string;
  unit?: string;
  printed_range_low?: number;
  printed_range_high?: number;
  raw_range?: string;
  status: ClinicalStatus;
  explanation?: string;
  confidence?: number;
}

export interface RedFlagAlert {
  biomarker: string;
  value: number | string;
  severity: 'critical' | 'urgent';
  action_prompt: string;
  message: string;
}

export interface MedicineInstruction {
  name: string;
  dosage?: string;
  frequency?: string;
  timing?: string;
  instructions?: string;
  plain_explanation?: string;
}

export interface ReportResult {
  document_id: string;
  status: 'ready' | 'processing' | 'unclear';
  requires_verification: boolean;
  disclaimer: string;
  biomarkers: BiomarkerValue[];
  medicines: MedicineInstruction[];
  red_flags: RedFlagAlert[];
  doctor_questions: string[];
  summary?: string;
  language: SupportedLanguage | string;
  reading_level: ReadingLevel | string;
}

export interface UserCorrectionPayload {
  document_id: string;
  corrected_text?: string;
  biomarkers?: BiomarkerValue[];
  medicines?: MedicineInstruction[];
  language?: SupportedLanguage | string;
  reading_level?: ReadingLevel | string;
}

export interface FeedbackPayload {
  rating: number;
  feedback?: string;
  document_id?: string;
}

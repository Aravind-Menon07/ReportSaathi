/**
 * ReportSaathi Frontend API Client.
 * Eliminates silent mock fallbacks: Throws descriptive errors if backend is unreachable on custom uploads.
 */

import { BiomarkerValue, MedicineInstruction, ReportResult } from './types';
import sampleReportData from '../../shared/sample-report.json';
import samplePrescriptionData from '../../shared/sample-prescription.json';

const API_BASE = '/api';

export async function checkBackendHealth(): Promise<{ healthy: boolean; service?: string }> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
    if (res.ok) {
      const data = await res.json();
      return { healthy: true, service: data.service };
    }
    return { healthy: false };
  } catch {
    return { healthy: false };
  }
}

export async function uploadDocument(file: File): Promise<{ document_id: string; filename: string; size_bytes: number }> {
  // Client-side 10 MB validation check
  if (file.size > 10 * 1024 * 1024) {
    throw new Error('File exceeds the 10 MB maximum allowed limit.');
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `Upload failed with status code ${res.status}`);
    }

    return await res.json();
  } catch (error: any) {
    if (error.message && error.message.includes('fetch')) {
      throw new Error('ReportSaathi backend is currently unreachable. Please ensure the backend server is running on http://localhost:8000.');
    }
    throw error;
  }
}

export async function extractDocumentText(documentId: string, rawText?: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, raw_text: rawText }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || 'Extraction failed.');
    }

    return await res.json();
  } catch (error: any) {
    if (error.message && error.message.includes('fetch')) {
      throw new Error('ReportSaathi backend is unreachable during OCR extraction.');
    }
    throw error;
  }
}

export async function submitCorrections(documentId: string, correctedText: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/extract/${documentId}/corrections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrected_text: correctedText }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || 'Failed to submit user corrections.');
    }

    return await res.json();
  } catch (error: any) {
    if (error.message && error.message.includes('fetch')) {
      throw new Error('ReportSaathi backend is unreachable during correction submission.');
    }
    throw error;
  }
}

export async function generateExplanations(
  documentId: string,
  biomarkers: BiomarkerValue[],
  language: string,
  readingLevel: string,
  medicines: MedicineInstruction[] = []
): Promise<ReportResult> {
  try {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
        biomarkers,
        medicines,
        language,
        reading_level: readingLevel,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || 'Explanation generation failed.');
    }

    return await res.json();
  } catch (error: any) {
    if (error.message && error.message.includes('fetch')) {
      throw new Error('ReportSaathi backend is unreachable during explanation generation.');
    }
    throw error;
  }
}

export async function loadSampleReport(): Promise<ReportResult> {
  // Returns the gold-standard CBC fixture from shared/sample-report.json
  return sampleReportData as unknown as ReportResult;
}

export async function loadSamplePrescription(): Promise<ReportResult> {
  // Returns the anonymized prescription demo fixture from shared/sample-prescription.json
  return samplePrescriptionData as unknown as ReportResult;
}


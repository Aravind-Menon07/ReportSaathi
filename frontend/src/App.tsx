import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { LanguageSelector } from './components/LanguageSelector';
import { UploadView } from './components/UploadView';
import { CheckValuesView } from './components/CheckValuesView';
import { ResultsView } from './components/ResultsView';
import { DoctorQuestionsView } from './components/DoctorQuestionsView';
import { ShareView } from './components/ShareView';

import {
  checkBackendHealth,
  uploadDocument,
  extractDocumentText,
  submitCorrections,
  generateExplanations,
  loadSampleReport,
} from './api';

import { SupportedLanguage, ReadingLevel, BiomarkerValue, ReportResult } from './types';

export const App: React.FC = () => {
  const [screen, setScreen] = useState<'upload' | 'check_values' | 'results' | 'questions' | 'share'>('upload');
  const [language, setLanguage] = useState<SupportedLanguage>('English');
  const [readingLevel, setReadingLevel] = useState<ReadingLevel>('Standard');
  const [backendHealthy, setBackendHealthy] = useState<boolean>(true);

  const [documentId, setDocumentId] = useState<string>('');
  const [rawText, setRawText] = useState<string>('');
  const [requiresVerification, setRequiresVerification] = useState<boolean>(false);
  const [biomarkers, setBiomarkers] = useState<BiomarkerValue[]>([]);
  const [reportResult, setReportResult] = useState<ReportResult | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  // Probe backend health on mount
  useEffect(() => {
    checkBackendHealth().then((res) => {
      setBackendHealthy(res.healthy);
    });
  }, []);

  const handleReset = () => {
    setScreen('upload');
    setDocumentId('');
    setRawText('');
    setRequiresVerification(false);
    setBiomarkers([]);
    setReportResult(null);
    setErrorMessage(undefined);
  };

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setErrorMessage(undefined);

    try {
      // Step 1: Upload file to backend
      const uploadRes = await uploadDocument(file);
      setDocumentId(uploadRes.document_id);

      // Step 2: OCR Extract & assess clarity
      const extractRes = await extractDocumentText(uploadRes.document_id);
      setRawText(extractRes.raw_text || '');
      setRequiresVerification(extractRes.requires_verification || false);
      setBiomarkers(extractRes.biomarkers || []);

      // Move to Step 2: Human verification screen
      setScreen('check_values');
    } catch (err: any) {
      setErrorMessage(err.message || 'Error uploading document.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadSample = async () => {
    setIsLoading(true);
    setErrorMessage(undefined);

    try {
      const sample = await loadSampleReport();
      setDocumentId(sample.document_id);
      setBiomarkers(sample.biomarkers);
      setReportResult(sample);
      setScreen('results');
    } catch (err: any) {
      setErrorMessage(err.message || 'Error loading sample report.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRawTextCorrection = async (correctedText: string) => {
    setIsLoading(true);
    try {
      const res = await submitCorrections(documentId, correctedText);
      setBiomarkers(res.biomarkers || []);
      setRequiresVerification(false);
    } catch (err: any) {
      alert(`Correction error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmValues = async (confirmedBiomarkers: BiomarkerValue[]) => {
    setIsLoading(true);
    setErrorMessage(undefined);

    try {
      const result = await generateExplanations(
        documentId,
        confirmedBiomarkers,
        language,
        readingLevel
      );
      setReportResult(result);
      setScreen('results');
    } catch (err: any) {
      alert(`Explanation error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header
        language={language}
        readingLevel={readingLevel}
        onReset={handleReset}
        backendHealthy={backendHealthy}
      />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8">
        {/* Global Language and Reading Depth Selector */}
        <LanguageSelector
          language={language}
          onLanguageChange={setLanguage}
          readingLevel={readingLevel}
          onReadingLevelChange={setReadingLevel}
        />

        {/* View Routing */}
        {screen === 'upload' && (
          <UploadView
            onFileUpload={handleFileUpload}
            onLoadSample={handleLoadSample}
            isLoading={isLoading}
            errorMessage={errorMessage}
            backendHealthy={backendHealthy}
          />
        )}

        {screen === 'check_values' && (
          <CheckValuesView
            initialBiomarkers={biomarkers}
            rawText={rawText}
            requiresVerification={requiresVerification}
            onConfirm={handleConfirmValues}
            onRawTextCorrection={handleRawTextCorrection}
          />
        )}

        {screen === 'results' && reportResult && (
          <ResultsView
            report={reportResult}
            onGoToQuestions={() => setScreen('questions')}
            onGoToShare={() => setScreen('share')}
          />
        )}

        {screen === 'questions' && reportResult && (
          <DoctorQuestionsView
            questions={reportResult.doctor_questions}
            onBack={() => setScreen('results')}
            onProceedToShare={() => setScreen('share')}
          />
        )}

        {screen === 'share' && reportResult && (
          <ShareView
            report={reportResult}
            onBack={() => setScreen('questions')}
          />
        )}
      </main>

      <Footer />
    </div>
  );
};

export default App;


import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertTriangle, ArrowRight, Sparkles, ShieldCheck, Activity, Pill } from 'lucide-react';

interface UploadViewProps {
  onFileUpload: (file: File) => void;
  onLoadSample: () => void;
  onLoadSamplePrescription: () => void;
  isLoading: boolean;
  errorMessage?: string;
  backendHealthy: boolean;
}

export const UploadView: React.FC<UploadViewProps> = ({
  onFileUpload,
  onLoadSample,
  onLoadSamplePrescription,
  isLoading,
  errorMessage,
  backendHealthy,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [consentGiven, setConsentGiven] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleSelectedFile(e.target.files[0]);
    }
  };

  const handleSelectedFile = (file: File) => {
    if (!consentGiven) {
      alert('Please check the consent box to proceed with ephemeral report explanation.');
      return;
    }
    onFileUpload(file);
  };

  return (
    <div className="space-y-6">
      {/* Intro hero banner */}
      <div className="bg-gradient-to-r from-teal-700 to-slate-800 rounded-3xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center space-x-1 px-3 py-1 bg-white/10 border border-white/20 rounded-full text-xs font-medium text-teal-200 mb-3">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Zero-Retention Ephemeral Pipeline</span>
          </span>
          <span className="inline-flex items-center space-x-1 ml-2 px-3 py-1 bg-white/10 border border-white/20 rounded-full text-xs font-medium text-teal-200 mb-3">
            <Activity className="w-3.5 h-3.5" />
            <span>Backend: {backendHealthy ? 'Connected' : 'Offline'}</span>
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Understand Your Medical Reports in Plain Language
          </h2>
          <p className="mt-2 text-teal-100/90 text-sm sm:text-base leading-relaxed">
            Upload your laboratory blood work or printed prescription slip. ReportSaathi reads printed values, verifies normal ranges directly from your document, and prepares questions for your doctor.
          </p>
        </div>
      </div>

      {/* Error notification if upload fails */}
      {errorMessage && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl p-4 flex items-start space-x-3 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Unable to process document</p>
            <p className="text-rose-700 mt-0.5">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Main Upload Dropzone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center cursor-pointer transition flex flex-col items-center justify-center bg-white ${
          dragActive
            ? 'border-teal-500 bg-teal-50/50 scale-[0.99]'
            : 'border-slate-300 hover:border-teal-400 hover:bg-slate-50/80 shadow-sm'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleChange}
          className="hidden"
          disabled={isLoading}
        />

        <div className="w-16 h-16 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mb-4 shadow-inner">
          <UploadCloud className="w-8 h-8" />
        </div>

        <h3 className="text-lg font-bold text-slate-800">
          Upload Medical Report or Prescription
        </h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Drag and drop your file here, or click to browse.
          <br />
          Supports <strong>PDF, JPG, PNG</strong> up to <strong>10 MB</strong>.
        </p>

        {isLoading ? (
          <div className="mt-6 flex items-center space-x-2 text-sm text-teal-700 font-medium">
            <div className="w-4 h-4 border-2 border-teal-600 border-t-transparent rounded-full animate-spin" />
            <span>Scanning and analyzing document with OCR...</span>
          </div>
        ) : (
          <button
            type="button"
            className="mt-6 inline-flex items-center space-x-2 px-5 py-2.5 bg-teal-600 text-white rounded-xl text-sm font-semibold hover:bg-teal-700 shadow-sm transition"
          >
            <span>Choose File</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* DPDP Consent Checkbox */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-start space-x-3 text-xs text-slate-600 shadow-sm">
        <input
          id="consent-check"
          type="checkbox"
          checked={consentGiven}
          onChange={(e) => setConsentGiven(e.target.checked)}
          className="mt-0.5 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
        />
        <label htmlFor="consent-check" className="cursor-pointer select-none">
          <strong>Patient Consent (DPDP Act 2023):</strong> I understand that ReportSaathi temporarily processes this uploaded document in memory to extract text and generate educational explanations. No medical records are permanently stored or shared for AI model training.
        </label>
      </div>

      {/* Quick Test Gold Standard Sample Button */}
      <div className="bg-slate-100 border border-slate-200 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-white text-teal-700 rounded-xl shadow-sm border border-slate-200">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">No report handy? Try a Sample CBC Report</h4>
            <p className="text-xs text-slate-500">Instant test using the adult Complete Blood Count gold-standard dataset.</p>
          </div>
        </div>

        <button
          type="button"
          onClick={onLoadSample}
          disabled={isLoading}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold shadow-sm transition shrink-0"
        >
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span>Load Gold-Standard Sample</span>
        </button>
      </div>

      {/* Prescription Sample Button */}
      <div className="bg-teal-50 border border-teal-200 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-white text-teal-700 rounded-xl shadow-sm border border-teal-200">
            <Pill className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">Try a Sample Prescription</h4>
            <p className="text-xs text-slate-500">Anonymized demo — Metformin, Amlodipine, Aspirin, Vitamin D3 explained in plain language.</p>
          </div>
        </div>

        <button
          type="button"
          onClick={onLoadSamplePrescription}
          disabled={isLoading}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow-sm transition shrink-0"
        >
          <Sparkles className="w-4 h-4 text-teal-200" />
          <span>Load Sample Prescription</span>
        </button>
      </div>
    </div>
  );
};

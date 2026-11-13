import React from 'react';
import { Printer, Share2, ArrowLeft } from 'lucide-react';
import { ReportResult } from '../types';

interface ShareViewProps {
  report: ReportResult;
  onBack: () => void;
}

export const ShareView: React.FC<ShareViewProps> = ({ report, onBack }) => {
  const handlePrint = () => {
    window.print();
  };

  const generateWhatsAppLink = () => {
    const questionsText = report.doctor_questions
      .map((q, idx) => `${idx + 1}. ${q}`)
      .join('\n');

    const message = `*ReportSaathi - Medical Report Summary*\n` +
      `Language: ${report.language} | Level: ${report.reading_level}\n\n` +
      `*Summary:* ${report.summary}\n\n` +
      `*Key Questions for Doctor:*\n${questionsText}\n\n` +
      `_Disclaimer: ${report.disclaimer}_`;

    return `https://api.whatsapp.com/send?text=${encodeURIComponent(message)}`;
  };

  return (
    <div className="space-y-6">
      {/* Top action controls (hidden when printing) */}
      <div className="no-print bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Share or Download Summary</h2>
          <p className="text-xs text-slate-500">Save a copy to your phone or send to your caregiver via WhatsApp</p>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <button
            type="button"
            onClick={handlePrint}
            className="flex-1 sm:flex-none inline-flex items-center justify-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Save PDF</span>
          </button>

          <a
            href={generateWhatsAppLink()}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 sm:flex-none inline-flex items-center justify-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
          >
            <Share2 className="w-4 h-4" />
            <span>Share via WhatsApp</span>
          </a>
        </div>
      </div>

      {/* Printable Sheet View */}
      <div className="printable-card bg-white border border-slate-200 rounded-3xl p-6 sm:p-10 shadow-sm space-y-6">
        {/* Printable Header */}
        <div className="border-b pb-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-black text-slate-900">ReportSaathi Medical Summary</h1>
            <p className="text-xs text-slate-500">
              Plain-Language Educational Report • Generated on {new Date().toLocaleDateString()}
            </p>
          </div>
          <div className="text-right text-xs text-slate-500">
            <p className="font-semibold text-slate-800">{report.language} Version</p>
            <p>{report.reading_level} Depth</p>
          </div>
        </div>

        {/* Mandatory Medical Disclaimer in Document */}
        <div className="bg-slate-100 border border-slate-300 p-3 rounded-xl text-xs text-slate-700 font-medium">
          <strong>Mandatory Notice:</strong> {report.disclaimer}
        </div>

        {/* Overview */}
        {report.summary && (
          <div className="space-y-1">
            <h3 className="text-xs font-bold uppercase text-slate-600 tracking-wider">Report Overview</h3>
            <p className="text-xs sm:text-sm text-slate-800 leading-relaxed">{report.summary}</p>
          </div>
        )}

        {/* Biomarkers Table */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase text-slate-600 tracking-wider">
            Biomarkers & Printed Normal Ranges
          </h3>
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <th className="py-2 px-3">Test Name</th>
                  <th className="py-2 px-3">Value</th>
                  <th className="py-2 px-3">Printed Range</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3">Plain-Language Meaning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report.biomarkers.map((b, i) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="py-2 px-3 font-semibold text-slate-800">{b.name}</td>
                    <td className="py-2 px-3 font-bold text-slate-900">
                      {b.value} {b.unit}
                    </td>
                    <td className="py-2 px-3 text-slate-600">{b.raw_range || 'None on report'}</td>
                    <td className="py-2 px-3 font-medium capitalize">
                      <span className={
                        b.status === 'normal' ? 'text-emerald-700 font-bold' :
                        b.status === 'borderline' ? 'text-amber-700 font-bold' :
                        b.status === 'needs_attention' ? 'text-rose-700 font-bold' : 'text-slate-500'
                      }>
                        {b.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-600 text-[11px] max-w-xs">{b.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Doctor Questions in Printable Sheet */}
        <div className="space-y-2 pt-2">
          <h3 className="text-xs font-bold uppercase text-slate-600 tracking-wider">
            Questions to Ask Your Doctor
          </h3>
          <ul className="list-decimal pl-5 space-y-1 text-xs text-slate-800 font-medium">
            {report.doctor_questions.map((q, idx) => (
              <li key={idx} className="leading-relaxed">{q}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Back button */}
      <div className="no-print pt-2">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center space-x-1.5 px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold shadow-sm transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Questions</span>
        </button>
      </div>
    </div>
  );
};

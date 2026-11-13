import React, { useState } from 'react';
import { Copy, Check, ArrowLeft, ArrowRight, MessageSquareQuote } from 'lucide-react';

interface DoctorQuestionsViewProps {
  questions: string[];
  onBack: () => void;
  onProceedToShare: () => void;
}

export const DoctorQuestionsView: React.FC<DoctorQuestionsViewProps> = ({
  questions,
  onBack,
  onProceedToShare,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const textToCopy = questions.map((q, idx) => `${idx + 1}. ${q}`).join('\n\n');
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-700 to-teal-900 rounded-3xl p-6 text-white shadow-md">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-white/10 rounded-xl">
            <MessageSquareQuote className="w-6 h-6 text-teal-200" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Questions to Ask Your Doctor</h2>
            <p className="text-xs text-teal-100">Make the most of your 5–10 minute doctor visit</p>
          </div>
        </div>
        <p className="text-xs text-teal-100/90 leading-relaxed max-w-2xl mt-2">
          These structured, non-directive questions are customized based on the out-of-range or borderline findings in your report. Bring them along to your consultation.
        </p>
      </div>

      {/* Copy Action Bar */}
      <div className="flex justify-between items-center px-1">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {questions.length} Prepared Consultation Questions
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-200 px-3 py-1.5 rounded-xl transition"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied to Clipboard!' : 'Copy All Questions'}</span>
        </button>
      </div>

      {/* Question Cards */}
      <div className="space-y-3">
        {questions.map((q, index) => (
          <div
            key={index}
            className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex items-start space-x-4 hover:border-teal-300 transition"
          >
            <div className="w-7 h-7 rounded-full bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
              {index + 1}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-800 leading-snug">{q}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Navigation Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-200">
        <button
          type="button"
          onClick={onBack}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold shadow-sm transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Explained Results</span>
        </button>

        <button
          type="button"
          onClick={onProceedToShare}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold shadow-md transition"
        >
          <span>Print Summary / Share</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

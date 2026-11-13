import React from 'react';
import { AlertOctagon, CheckCircle2, AlertTriangle, HelpCircle, ArrowRight, FileDown } from 'lucide-react';
import { ReportResult, BiomarkerValue, RedFlagAlert } from '../types';

interface ResultsViewProps {
  report: ReportResult;
  onGoToQuestions: () => void;
  onGoToShare: () => void;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  report,
  onGoToQuestions,
  onGoToShare,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'normal':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Within Normal Range</span>
          </span>
        );
      case 'borderline':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Near Range Boundary</span>
          </span>
        );
      case 'needs_attention':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Outside Printed Range</span>
          </span>
        );
      case 'no_range_on_report':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>No Range on Report</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. CRITICAL RED-FLAG EMERGENCY ALERT BANNER (At Top, Non-Negotiable) */}
      {report.red_flags && report.red_flags.length > 0 && (
        <div className="bg-rose-600 text-white rounded-3xl p-6 shadow-xl border-4 border-rose-700 animate-pulse">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-white/20 rounded-2xl shrink-0">
              <AlertOctagon className="w-8 h-8 text-white" />
            </div>
            <div className="space-y-2">
              <span className="inline-block px-3 py-0.5 bg-white text-rose-700 text-xs font-extrabold uppercase tracking-wider rounded-full">
                Critical Medical Alert
              </span>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight">
                Emergency Attention Required
              </h2>
              <p className="text-rose-100 text-sm">
                One or more laboratory values on this report meet critical thresholds that require immediate medical evaluation by a qualified doctor or emergency clinic.
              </p>

              <div className="space-y-2 pt-2">
                {report.red_flags.map((alert: RedFlagAlert, i: number) => (
                  <div
                    key={i}
                    className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-3 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between font-bold text-white">
                      <span>{alert.biomarker}: {alert.value}</span>
                      <span className="uppercase text-[10px] bg-rose-800 px-2 py-0.5 rounded-full">Immediate</span>
                    </div>
                    <p className="text-rose-100">{alert.action_prompt}</p>
                    <p className="text-rose-200/80 italic">{alert.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Box */}
      {report.summary && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Report Overview ({report.language} • {report.reading_level})
          </h3>
          <p className="text-sm text-slate-700 leading-relaxed">{report.summary}</p>
        </div>
      )}

      {/* Biomarker Cards Grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-800 tracking-wide uppercase">
          Explained Laboratory Parameters ({report.biomarkers.length})
        </h3>

        <div className="grid grid-cols-1 gap-4">
          {report.biomarkers.map((b: BiomarkerValue, idx: number) => (
            <div
              key={idx}
              className={`bg-white rounded-2xl p-5 border shadow-sm transition ${
                b.status === 'needs_attention'
                  ? 'border-rose-200 ring-1 ring-rose-100'
                  : b.status === 'borderline'
                  ? 'border-amber-200 ring-1 ring-amber-100'
                  : 'border-slate-200'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                <div>
                  <h4 className="text-base font-bold text-slate-900">{b.name}</h4>
                  <p className="text-xs text-slate-500">
                    Printed Normal Range:{' '}
                    <span className="font-semibold text-slate-700">
                      {b.raw_range ? b.raw_range : 'Not specified on report'}
                    </span>
                  </p>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <span className="text-lg font-black text-slate-900">{b.value}</span>
                    {b.unit && <span className="text-xs text-slate-500 ml-1 font-medium">{b.unit}</span>}
                  </div>
                  {getStatusBadge(b.status)}
                </div>
              </div>

              {b.explanation && (
                <div className="mt-3 text-xs sm:text-sm text-slate-600 leading-relaxed bg-slate-50/70 p-3.5 rounded-xl border border-slate-100">
                  <p>{b.explanation}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom CTA Row */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-200">
        <button
          type="button"
          onClick={onGoToShare}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-5 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold shadow-sm transition"
        >
          <FileDown className="w-4 h-4 text-teal-600" />
          <span>Download PDF / Share</span>
        </button>

        <button
          type="button"
          onClick={onGoToQuestions}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold shadow-md transition"
        >
          <span>View Doctor Consultation Questions</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

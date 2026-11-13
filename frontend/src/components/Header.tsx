import React from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { SupportedLanguage, ReadingLevel } from '../types';

interface HeaderProps {
  language: SupportedLanguage | string;
  readingLevel: ReadingLevel | string;
  onReset: () => void;
  backendHealthy: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  readingLevel,
  onReset,
  backendHealthy,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={onReset}>
          <div className="bg-teal-600 text-white p-2 rounded-xl shadow-sm">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">ReportSaathi</h1>
              <span className="text-xs font-semibold px-2 py-0.5 bg-teal-50 text-teal-700 border border-teal-200 rounded-full">
                रिपोर्ट साथी
              </span>
            </div>
            <p className="text-xs text-slate-500">Plain-Language Medical Report Explainer</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg">
            <span className="font-medium text-slate-800">{language}</span>
            <span>•</span>
            <span className="text-slate-600">{readingLevel}</span>
          </div>

          <div className="flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-lg border font-medium">
            <span
              className={`w-2 h-2 rounded-full ${
                backendHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`}
            />
            <span className={backendHealthy ? 'text-emerald-700' : 'text-amber-700'}>
              {backendHealthy ? 'API Active' : 'Offline'}
            </span>
          </div>

          <button
            onClick={onReset}
            className="flex items-center space-x-1 text-xs text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg transition"
            title="Start over with a new report"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden md:inline">New Report</span>
          </button>
        </div>
      </div>
    </header>
  );
};

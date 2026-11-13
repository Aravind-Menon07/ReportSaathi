import React from 'react';
import { Languages, BookOpen } from 'lucide-react';
import { SupportedLanguage, ReadingLevel } from '../types';

interface LanguageSelectorProps {
  language: SupportedLanguage | string;
  onLanguageChange: (lang: SupportedLanguage) => void;
  readingLevel: ReadingLevel | string;
  onReadingLevelChange: (level: ReadingLevel) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  language,
  onLanguageChange,
  readingLevel,
  onReadingLevelChange,
}) => {
  const languages: { key: SupportedLanguage; label: string; native: string }[] = [
    { key: 'English', label: 'English', native: 'English' },
    { key: 'Hindi', label: 'Hindi', native: 'हिन्दी' },
    { key: 'Kannada', label: 'Kannada', native: 'ಕನ್ನಡ' },
  ];

  const levels: { key: ReadingLevel; label: string; desc: string }[] = [
    { key: 'Simple', label: 'Simple', desc: 'Grade 5 level, everyday analogies' },
    { key: 'Standard', label: 'Standard', desc: 'Clear, balanced explanation' },
    { key: 'Detailed', label: 'Detailed', desc: 'Comprehensive physiological context' },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm mb-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Language Selection */}
        <div>
          <div className="flex items-center space-x-2 mb-2.5">
            <Languages className="w-4 h-4 text-teal-600" />
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Preferred Language
            </label>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {languages.map((l) => (
              <button
                key={l.key}
                type="button"
                onClick={() => onLanguageChange(l.key)}
                className={`flex flex-col items-center justify-center py-2 px-3 rounded-xl border text-center transition ${
                  language === l.key
                    ? 'bg-teal-600 text-white border-teal-600 shadow-sm font-semibold'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <span className="text-sm font-medium">{l.label}</span>
                <span className={`text-xs ${language === l.key ? 'text-teal-100' : 'text-slate-400'}`}>
                  {l.native}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Reading Level Selection */}
        <div>
          <div className="flex items-center space-x-2 mb-2.5">
            <BookOpen className="w-4 h-4 text-teal-600" />
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Explanation Depth
            </label>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {levels.map((lvl) => (
              <button
                key={lvl.key}
                type="button"
                onClick={() => onReadingLevelChange(lvl.key)}
                className={`flex flex-col items-center justify-center py-2 px-2.5 rounded-xl border text-center transition ${
                  readingLevel === lvl.key
                    ? 'bg-teal-600 text-white border-teal-600 shadow-sm font-semibold'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
                title={lvl.desc}
              >
                <span className="text-sm font-medium">{lvl.label}</span>
                <span className={`text-[10px] truncate max-w-full ${readingLevel === lvl.key ? 'text-teal-100' : 'text-slate-400'}`}>
                  {lvl.desc.split(',')[0]}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

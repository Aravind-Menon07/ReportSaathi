import React from 'react';
import { AlertCircle, Lock, Shield } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 mt-auto border-t border-slate-800 text-xs py-6">
      <div className="max-w-5xl mx-auto px-4 space-y-4">
        {/* MANDATORY MEDICAL DISCLAIMER BANNER (docs/06b) */}
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex items-start space-x-3 text-amber-200">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-300 text-sm">
              This explains your report. It does not replace your doctor.
            </p>
            <p className="text-amber-200/80 mt-0.5">
              ReportSaathi is an educational health literacy tool. It does not diagnose diseases, recommend medications, or alter dosages. Always consult your qualified healthcare provider for clinical evaluation.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between pt-2 border-t border-slate-800 text-slate-400 space-y-2 sm:space-y-0">
          <div className="flex items-center space-x-2">
            <Lock className="w-3.5 h-3.5 text-teal-400" />
            <span>DPDP Act (2023) Aligned • Ephemeral Processing • Zero Long-Term Storage</span>
          </div>
          <div className="flex items-center space-x-1">
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            <span>Open Source Healthcare Initiative</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

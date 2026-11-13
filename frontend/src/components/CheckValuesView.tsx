import React, { useState } from 'react';
import { AlertTriangle, Plus, Trash2, ArrowRight, Edit3 } from 'lucide-react';
import { BiomarkerValue } from '../types';

interface CheckValuesViewProps {
  initialBiomarkers: BiomarkerValue[];
  rawText?: string;
  requiresVerification: boolean;
  onConfirm: (biomarkers: BiomarkerValue[]) => void;
  onRawTextCorrection: (correctedText: string) => void;
}

export const CheckValuesView: React.FC<CheckValuesViewProps> = ({
  initialBiomarkers,
  rawText = '',
  requiresVerification,
  onConfirm,
  onRawTextCorrection,
}) => {
  const [biomarkers, setBiomarkers] = useState<BiomarkerValue[]>(initialBiomarkers);
  const [showRawEditor, setShowRawEditor] = useState(false);
  const [editableRawText, setEditableRawText] = useState(rawText);

  const handleUpdate = (index: number, field: keyof BiomarkerValue, val: any) => {
    const updated = [...biomarkers];
    updated[index] = { ...updated[index], [field]: val };
    setBiomarkers(updated);
  };

  const handleAddRow = () => {
    setBiomarkers([
      ...biomarkers,
      {
        name: 'New Test',
        value: 0,
        unit: 'mg/dL',
        printed_range_low: 0,
        printed_range_high: 100,
        raw_range: '0 - 100',
        status: 'normal',
      },
    ]);
  };

  const handleRemoveRow = (index: number) => {
    setBiomarkers(biomarkers.filter((_, i) => i !== index));
  };

  const handleApplyRawText = () => {
    onRawTextCorrection(editableRawText);
    setShowRawEditor(false);
  };

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-6 h-6 rounded-full bg-teal-600 text-white text-xs font-bold flex items-center justify-center">
              2
            </span>
            <h2 className="text-xl font-bold text-slate-900">Verify Extracted Lab Values</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Please compare the values extracted below against your original printed document before generating explanations.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowRawEditor(!showRawEditor)}
          className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-xl transition self-start sm:self-auto"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>{showRawEditor ? 'Hide Raw Text' : 'Edit Full OCR Text'}</span>
        </button>
      </div>

      {/* Verification Warning if noise or blurry tokens detected */}
      {requiresVerification && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-2xl p-4 flex items-start space-x-3 text-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Notice: Visual Noise Detected in Document</p>
            <p className="text-amber-700 text-xs mt-0.5">
              The OCR scanner detected potential low-contrast or noisy text. Double-check the numbers below to ensure accuracy.
            </p>
          </div>
        </div>
      )}

      {/* EMPTY STATE WARNING BANNER (Required for non-medical photos) */}
      {biomarkers.length === 0 && (
        <div className="bg-rose-50 border-2 border-dashed border-rose-300 rounded-2xl p-6 text-center space-y-3">
          <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center mx-auto">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-rose-900">No Medical Lab Values Detected</h3>
          <p className="text-xs text-rose-700 max-w-md mx-auto">
            ReportSaathi could not locate recognizable laboratory parameters or printed ranges on this document. This usually occurs if a non-medical photo or illegible scan was uploaded.
          </p>
          <div className="pt-2 flex justify-center space-x-3">
            <button
              type="button"
              onClick={handleAddRow}
              className="inline-flex items-center space-x-1 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-semibold hover:bg-rose-700 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Manually Enter a Lab Value</span>
            </button>
          </div>
        </div>
      )}

      {/* Raw Text Editor Modal / Section */}
      {showRawEditor && (
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3 shadow-inner">
          <label className="text-xs font-bold text-slate-700 block">
            Extracted Document Text (Edit and click Apply to re-parse):
          </label>
          <textarea
            rows={6}
            value={editableRawText}
            onChange={(e) => setEditableRawText(e.target.value)}
            className="w-full text-xs font-mono p-3 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleApplyRawText}
            className="px-4 py-2 bg-teal-600 text-white rounded-xl text-xs font-semibold hover:bg-teal-700 transition shadow-sm"
          >
            Apply Corrections & Re-Parse
          </button>
        </div>
      )}

      {/* Editable Table */}
      {biomarkers.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <th className="py-3 px-4">Test Name</th>
                  <th className="py-3 px-4 w-28">Observed Value</th>
                  <th className="py-3 px-4 w-24">Unit</th>
                  <th className="py-3 px-4 w-36">Printed Normal Range</th>
                  <th className="py-3 px-4 w-12 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {biomarkers.map((b, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-4">
                      <input
                        type="text"
                        value={b.name}
                        onChange={(e) => handleUpdate(idx, 'name', e.target.value)}
                        className="w-full font-medium text-slate-800 bg-transparent border-b border-transparent focus:border-teal-500 focus:outline-none"
                      />
                    </td>
                    <td className="py-2.5 px-4">
                      <input
                        type="text"
                        value={b.value}
                        onChange={(e) => handleUpdate(idx, 'value', e.target.value)}
                        className="w-full font-bold text-slate-900 bg-slate-50 px-2 py-1 rounded border border-slate-200 focus:border-teal-500 focus:outline-none"
                      />
                    </td>
                    <td className="py-2.5 px-4">
                      <input
                        type="text"
                        value={b.unit || ''}
                        onChange={(e) => handleUpdate(idx, 'unit', e.target.value)}
                        className="w-full text-slate-500 bg-transparent border-b border-transparent focus:border-teal-500 focus:outline-none"
                      />
                    </td>
                    <td className="py-2.5 px-4">
                      <input
                        type="text"
                        value={b.raw_range || ''}
                        onChange={(e) => handleUpdate(idx, 'raw_range', e.target.value)}
                        placeholder="e.g. 12.0 - 15.5"
                        className="w-full text-slate-600 bg-slate-50 px-2 py-1 rounded border border-slate-200 focus:border-teal-500 focus:outline-none"
                      />
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <button
                        type="button"
                        onClick={() => handleRemoveRow(idx)}
                        className="text-slate-400 hover:text-rose-600 transition p-1"
                        title="Delete this row"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-slate-50 border-t border-slate-200 flex justify-between items-center">
            <button
              type="button"
              onClick={handleAddRow}
              className="inline-flex items-center space-x-1 text-xs text-teal-700 font-semibold hover:text-teal-800 px-3 py-1.5 rounded-lg hover:bg-teal-50 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Another Test</span>
            </button>
            <span className="text-[11px] text-slate-500">
              {biomarkers.length} parameter{biomarkers.length === 1 ? '' : 's'} identified
            </span>
          </div>
        </div>
      )}

      {/* Action Footer */}
      <div className="flex justify-end pt-2">
        <button
          type="button"
          onClick={() => onConfirm(biomarkers)}
          disabled={biomarkers.length === 0}
          className="inline-flex items-center space-x-2 px-6 py-3 bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-xl text-sm font-bold shadow-md transition"
        >
          <span>Confirm & Generate Explanations</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

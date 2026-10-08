'use client';

import { ResearchReport } from '@/lib/types';
import { FileText, Printer, AlertTriangle, Clock, Bot, FileSignature, Loader2 } from 'lucide-react';
import FreshnessLabel from './FreshnessLabel';
import { useState } from 'react';
import { api } from '@/lib/api';

export default function ResearchReportDisplay({ symbol, initialReport }: { symbol: string, initialReport?: ResearchReport }) {
  const [report, setReport] = useState<ResearchReport | undefined>(initialReport);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const newReport = await api.generateReport(symbol);
      setReport(newReport);
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (!report && !isGenerating) {
    return (
      <div className="bg-card border border-border rounded-lg p-12 text-center shadow-sm">
        <div className="mx-auto w-16 h-16 bg-background rounded-full flex items-center justify-center mb-4">
          <FileText className="h-8 w-8 text-gray-500" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">No Research Report Available</h3>
        <p className="text-sm text-gray-400 mb-6 max-w-md mx-auto">
          Generate an automated research report for {symbol} combining technical analysis and fundamental data.
        </p>
        {error && <div className="text-bearish text-sm mb-4">{error}</div>}
        <button 
          onClick={handleGenerate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <FileSignature className="h-4 w-4" />
          Generate Report
        </button>
      </div>
    );
  }

  if (isGenerating) {
    return (
      <div className="bg-card border border-border rounded-lg p-16 text-center shadow-sm">
        <Loader2 className="h-8 w-8 text-primary animate-spin mx-auto mb-4" />
        <h3 className="text-lg font-medium text-foreground mb-2">Generating Report...</h3>
        <p className="text-sm text-gray-400">
          Analyzing technical indicators, financial ratios, and market data for {symbol}. This may take a few moments.
        </p>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm print:shadow-none print:border-none print:bg-white print:text-black">
      {/* Action Bar - Hidden on Print */}
      <div className="flex justify-between items-center p-4 border-b border-border print:hidden bg-background/50 rounded-t-lg">
        <div className="flex gap-3">
          <div className="px-2 py-1 bg-card border border-border rounded text-xs text-gray-400 flex items-center gap-1.5">
            <Clock className="h-3 w-3" />
            Generated: {new Date(report.generated_at).toLocaleString()}
          </div>
          <div className="px-2 py-1 bg-card border border-border rounded text-xs text-gray-400 flex items-center gap-1.5 capitalize">
            {report.generation_method === 'llm' ? <Bot className="h-3 w-3 text-purple-400" /> : <FileSignature className="h-3 w-3 text-blue-400" />}
            {report.generation_method} Generation
          </div>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleGenerate}
            disabled={isGenerating}
            className="px-3 py-1.5 bg-background border border-border hover:bg-border rounded text-sm text-foreground transition-colors"
          >
            Regenerate
          </button>
          <button 
            onClick={handlePrint}
            className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90 transition-colors flex items-center gap-1.5"
          >
            <Printer className="h-4 w-4" /> Print
          </button>
        </div>
      </div>

      {/* Freshness Warning Banner */}
      {report.data_freshness.overall_quality !== 'excellent' && (
        <div className="bg-neutral/10 border-b border-neutral/20 p-3 px-6 flex items-start gap-3 print:bg-gray-100 print:text-gray-800">
          <AlertTriangle className="h-5 w-5 text-neutral shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold text-neutral print:text-gray-800 mb-1">Data Quality Warning: {report.data_freshness.overall_quality.toUpperCase()}</p>
            <p className="text-gray-400 print:text-gray-600 text-xs">
              This report may be based on incomplete or outdated data. 
              {report.data_freshness.quote_age_seconds && report.data_freshness.quote_age_seconds > 86400 ? ' Market data is stale.' : ''}
              {!report.data_freshness.fundamentals_last_date ? ' Fundamental data is missing.' : ''}
            </p>
          </div>
        </div>
      )}

      {/* Report Content */}
      <div className="p-8 print:p-0 prose prose-invert max-w-none print:prose-p:text-black print:prose-headings:text-black">
        <h1 className="text-3xl font-bold border-b border-border pb-4 mb-8 print:border-black print:pb-2">
          Automated Research Report: {report.symbol}
        </h1>

        <div className="space-y-8">
          {report.sections.map((section, idx) => (
            <section key={idx} className="break-inside-avoid">
              <h2 className="text-xl font-semibold text-primary mb-4 print:text-blue-800">{section.title}</h2>
              <div className="text-gray-300 leading-relaxed whitespace-pre-wrap print:text-gray-800 text-sm">
                {section.content}
              </div>
              
              {/* Optional data points rendering */}
              {section.data_points && section.data_points.length > 0 && (
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                  {section.data_points.map((dp, i) => (
                    <div key={i} className="bg-background border border-border p-3 rounded print:border-gray-300">
                      <div className="text-xs text-gray-500 uppercase">{dp.label}</div>
                      <div className="font-mono text-lg">{dp.value}</div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>

        <div className="mt-12 pt-6 border-t border-border text-xs text-gray-500 print:text-gray-500 print:border-gray-300">
          <p><strong>Disclaimer:</strong> This report is generated automatically by algorithms and/or AI models based on available market and fundamental data. It does not constitute financial advice. Always conduct your own research before making investment decisions.</p>
          <p className="mt-2">Generated on NSE Analysis Platform • {new Date(report.generated_at).toUTCString()}</p>
        </div>
      </div>
    </div>
  );
}

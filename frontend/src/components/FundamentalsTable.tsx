'use client';

import { FundamentalData, FinancialRatio } from '@/lib/types';
import { useState } from 'react';
import Link from 'next/link';
import { Info, ExternalLink } from 'lucide-react';

export default function FundamentalsTable({ data, isLoading }: { data?: FundamentalData, isLoading?: boolean }) {
  const [activeTab, setActiveTab] = useState<'ratios' | 'income' | 'balance' | 'cash'>('ratios');

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 animate-pulse">
        <div className="flex gap-4 mb-6 border-b border-border pb-2">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-6 w-24 bg-border/50 rounded"></div>)}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map(i => <div key={i} className="h-24 bg-border/30 rounded"></div>)}
        </div>
      </div>
    );
  }

  if (!data || (!data.ratios?.length && !data.statements?.length)) {
    return (
      <div className="bg-card border border-border rounded-lg p-12 text-center shadow-sm">
        <h3 className="text-lg font-medium text-foreground mb-2">Fundamental Data Not Available</h3>
        <p className="text-sm text-gray-400 mb-6 max-w-md mx-auto">
          We don't have fundamental data for this stock yet. You can import financial data via CSV in the settings.
        </p>
        <Link href="/settings" className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors">
          Go to Settings
        </Link>
      </div>
    );
  }

  const renderRatios = () => {
    if (!data.ratios || data.ratios.length === 0) {
      return <div className="text-center text-gray-400 py-8">No ratio data available</div>;
    }

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {data.ratios.map((ratio, i) => (
          <div key={i} className="bg-background border border-border rounded-lg p-4 relative group">
            {!ratio.is_meaningful && (
              <div className="absolute top-2 right-2 bg-neutral/20 text-neutral text-[10px] px-1.5 py-0.5 rounded" title="Value cannot be calculated meaningfully (e.g. negative P/E)">
                NM
              </div>
            )}
            <h4 className="text-xs text-gray-400 font-medium uppercase tracking-wider mb-1 pr-6" title={ratio.formula}>
              {ratio.name}
            </h4>
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-semibold text-foreground">
                {ratio.value !== null ? ratio.value.toFixed(2) : 'N/A'}
              </span>
              <span className="text-xs text-gray-500">{ratio.unit}</span>
            </div>
            <div className="mt-2 text-[10px] text-gray-500 flex items-center justify-between">
              <span>{ratio.period_type} • {ratio.period}</span>
              {ratio.formula && (
                <Info className="h-3 w-3 text-gray-400 cursor-help" title={ratio.formula} />
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderStatements = (type: string) => {
    // Placeholder for actual statement rendering logic based on structure
    return (
      <div className="text-center text-gray-400 py-12 border border-dashed border-border rounded-lg">
        Detailed statement view coming soon.
      </div>
    );
  };

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
      <div className="flex overflow-x-auto border-b border-border bg-background/50">
        <button 
          onClick={() => setActiveTab('ratios')}
          className={`px-6 py-3 text-sm font-medium whitespace-nowrap transition-colors ${activeTab === 'ratios' ? 'border-b-2 border-primary text-primary' : 'text-gray-400 hover:text-foreground'}`}
        >
          Key Ratios
        </button>
        <button 
          onClick={() => setActiveTab('income')}
          className={`px-6 py-3 text-sm font-medium whitespace-nowrap transition-colors ${activeTab === 'income' ? 'border-b-2 border-primary text-primary' : 'text-gray-400 hover:text-foreground'}`}
        >
          Income Statement
        </button>
        <button 
          onClick={() => setActiveTab('balance')}
          className={`px-6 py-3 text-sm font-medium whitespace-nowrap transition-colors ${activeTab === 'balance' ? 'border-b-2 border-primary text-primary' : 'text-gray-400 hover:text-foreground'}`}
        >
          Balance Sheet
        </button>
        <button 
          onClick={() => setActiveTab('cash')}
          className={`px-6 py-3 text-sm font-medium whitespace-nowrap transition-colors ${activeTab === 'cash' ? 'border-b-2 border-primary text-primary' : 'text-gray-400 hover:text-foreground'}`}
        >
          Cash Flow
        </button>
      </div>

      <div className="p-6">
        {activeTab === 'ratios' ? renderRatios() : renderStatements(activeTab)}
      </div>
    </div>
  );
}

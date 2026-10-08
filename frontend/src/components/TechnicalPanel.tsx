'use client';

import { TechnicalIndicator } from '@/lib/types';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';

export default function TechnicalPanel({ data, isLoading }: { data?: TechnicalIndicator[], isLoading?: boolean }) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="bg-card border border-border rounded-lg p-4 h-32"></div>
        ))}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-8 text-center text-gray-400">
        No technical indicators available.
      </div>
    );
  }

  // Count signals
  const bullish = data.filter(i => i.signal === 'bullish').length;
  const bearish = data.filter(i => i.signal === 'bearish').length;
  const neutral = data.filter(i => i.signal === 'neutral').length;

  let overallSignal = 'Neutral';
  let overallColor = 'text-neutral';
  let overallBg = 'bg-neutral/10';
  
  if (bullish > bearish + 2) { overallSignal = 'Strong Buy'; overallColor = 'text-bullish'; overallBg = 'bg-bullish/10'; }
  else if (bullish > bearish) { overallSignal = 'Buy'; overallColor = 'text-bullish'; overallBg = 'bg-bullish/10'; }
  else if (bearish > bullish + 2) { overallSignal = 'Strong Sell'; overallColor = 'text-bearish'; overallBg = 'bg-bearish/10'; }
  else if (bearish > bullish) { overallSignal = 'Sell'; overallColor = 'text-bearish'; overallBg = 'bg-bearish/10'; }

  const formatValue = (val: number | null) => {
    if (val === null) return 'N/A';
    return val.toFixed(2);
  };

  const getSignalIcon = (signal: string) => {
    if (signal === 'bullish') return <TrendingUp className="h-4 w-4 text-bullish" />;
    if (signal === 'bearish') return <TrendingDown className="h-4 w-4 text-bearish" />;
    return <Minus className="h-4 w-4 text-neutral" />;
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'bullish') return 'text-bullish bg-bullish/10';
    if (signal === 'bearish') return 'text-bearish bg-bearish/10';
    return 'text-neutral bg-neutral/10';
  };

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="bg-card border border-border rounded-lg p-6 flex flex-col md:flex-row justify-between items-center gap-4 shadow-sm">
        <div>
          <h3 className="text-lg font-semibold mb-1">Technical Summary</h3>
          <p className="text-sm text-gray-400">Based on Daily timeframe</p>
        </div>
        <div className="flex gap-4 items-center">
          <div className="text-center px-4 border-r border-border">
            <div className="text-2xl font-bold text-bullish">{bullish}</div>
            <div className="text-xs text-gray-400 uppercase">Bullish</div>
          </div>
          <div className="text-center px-4 border-r border-border">
            <div className="text-2xl font-bold text-neutral">{neutral}</div>
            <div className="text-xs text-gray-400 uppercase">Neutral</div>
          </div>
          <div className="text-center px-4">
            <div className="text-2xl font-bold text-bearish">{bearish}</div>
            <div className="text-xs text-gray-400 uppercase">Bearish</div>
          </div>
        </div>
        <div className={`px-6 py-3 rounded-lg flex flex-col items-center ${overallBg}`}>
          <span className="text-xs font-medium text-gray-500 uppercase mb-1">Overall Signal</span>
          <span className={`text-xl font-bold ${overallColor}`}>{overallSignal}</span>
        </div>
      </div>

      {/* Indicators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((ind, i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-5 shadow-sm relative overflow-hidden group">
            {!ind.sufficient_data && (
              <div className="absolute top-0 right-0 bg-neutral/20 text-neutral text-[10px] px-2 py-0.5 rounded-bl font-medium flex items-center gap-1">
                <Info className="h-3 w-3" /> Insufficient Data
              </div>
            )}
            
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-foreground" title={ind.name}>{ind.name}</h4>
              <span className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 capitalize ${getSignalColor(ind.signal)}`}>
                {getSignalIcon(ind.signal)} {ind.signal}
              </span>
            </div>
            
            <div className="text-2xl font-mono mb-2">
              {formatValue(ind.value)}
            </div>
            
            <p className="text-xs text-gray-400 leading-relaxed">
              {ind.description}
            </p>
            
            {!ind.sufficient_data && (
              <p className="text-[10px] text-neutral mt-2">
                Needs {ind.periods_required} periods, has {ind.periods_available}.
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

'use client';

import React from 'react';

type FreshnessLabelProps = {
  data_quality?: 'live' | 'delayed' | 'eod' | 'stale' | 'demo';
  fetch_timestamp?: string;
  source_timestamp?: string | null;
};

export default function FreshnessLabel({ data_quality, fetch_timestamp, source_timestamp }: FreshnessLabelProps) {
  if (!data_quality) return null;

  const getBadgeProps = () => {
    switch (data_quality) {
      case 'live':
        return { color: 'bg-bullish', text: 'Live', dot: true, pulse: true };
      case 'delayed':
        return { color: 'bg-neutral', text: 'Delayed', dot: true, pulse: false };
      case 'eod':
        return { color: 'bg-info', text: 'EOD', dot: true, pulse: false };
      case 'stale':
        return { color: 'bg-bearish', text: 'Stale', dot: true, pulse: false };
      case 'demo':
        return { color: 'bg-gray-500', text: 'Demo', dot: true, pulse: false };
      default:
        return { color: 'bg-gray-500', text: 'Unknown', dot: false, pulse: false };
    }
  };

  const badge = getBadgeProps();
  
  // Calculate age if we have a fetch timestamp
  let ageStr = '';
  if (fetch_timestamp) {
    const fetchTime = new Date(fetch_timestamp).getTime();
    const now = new Date().getTime();
    const diffSeconds = Math.floor((now - fetchTime) / 1000);
    
    if (diffSeconds < 60) {
      ageStr = 'just now';
    } else if (diffSeconds < 3600) {
      ageStr = `${Math.floor(diffSeconds / 60)}m ago`;
    } else if (diffSeconds < 86400) {
      ageStr = `${Math.floor(diffSeconds / 3600)}h ago`;
    } else {
      ageStr = `${Math.floor(diffSeconds / 86400)}d ago`;
    }
  }

  const tooltipText = `Fetched: ${fetch_timestamp ? new Date(fetch_timestamp).toLocaleString() : 'Unknown'}${source_timestamp ? `\nSource: ${new Date(source_timestamp).toLocaleString()}` : ''}`;

  return (
    <div 
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-medium bg-card border border-border cursor-help"
      title={tooltipText}
    >
      {badge.dot && (
        <span className="relative flex h-2 w-2">
          {badge.pulse && <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${badge.color}`}></span>}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${badge.color}`}></span>
        </span>
      )}
      <span className="text-gray-300">{badge.text}</span>
      {ageStr && data_quality === 'stale' && (
        <span className="text-gray-400 ml-0.5">({ageStr})</span>
      )}
    </div>
  );
}

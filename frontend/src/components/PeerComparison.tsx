'use client';

import { PeerData } from '@/lib/types';
import Link from 'next/link';
import { ArrowUpDown } from 'lucide-react';
import { useState } from 'react';

type SortKey = keyof PeerData;
type SortOrder = 'asc' | 'desc';

export default function PeerComparison({ data, currentSymbol, isLoading }: { data?: PeerData[], currentSymbol: string, isLoading?: boolean }) {
  const [sortKey, setSortKey] = useState<SortKey>('market_cap');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 animate-pulse">
        <div className="h-8 bg-border/50 border-b border-border mb-4"></div>
        {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-12 border-b border-border/30 bg-background/50 mb-1"></div>)}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-8 text-center text-gray-400">
        No peer comparison data available for this stock.
      </div>
    );
  }

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc'); // Default to desc for most financial metrics
    }
  };

  const sortedData = [...data].sort((a, b) => {
    const valA = a[sortKey];
    const valB = b[sortKey];
    
    if (valA === null && valB === null) return 0;
    if (valA === null) return 1; // nulls always at bottom
    if (valB === null) return -1;
    
    if (typeof valA === 'string' && typeof valB === 'string') {
      return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    
    if (typeof valA === 'number' && typeof valB === 'number') {
      return sortOrder === 'asc' ? valA - valB : valB - valA;
    }
    
    return 0;
  });

  const formatNumber = (val: number | null, type: 'currency' | 'percent' | 'ratio' = 'ratio') => {
    if (val === null) return '-';
    if (type === 'currency') return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (type === 'percent') return `${val > 0 ? '+' : ''}${val.toFixed(2)}%`;
    return val.toFixed(2);
  };

  // Find min/max for highlighting
  const getHighlightClass = (key: keyof PeerData, value: number | null, isHigherBetter: boolean = true) => {
    if (value === null) return '';
    
    const validValues = data.map(d => d[key]).filter(v => v !== null) as number[];
    if (validValues.length < 2) return '';
    
    const max = Math.max(...validValues);
    const min = Math.min(...validValues);
    
    if (value === max) return isHigherBetter ? 'text-bullish font-semibold' : 'text-bearish font-semibold';
    if (value === min) return isHigherBetter ? 'text-bearish font-semibold' : 'text-bullish font-semibold';
    return '';
  };

  const SortHeader = ({ label, sortKey: key }: { label: string, sortKey: SortKey }) => (
    <th 
      className="px-4 py-3 text-right font-medium cursor-pointer hover:bg-background/80 transition-colors group"
      onClick={() => handleSort(key)}
    >
      <div className="flex items-center justify-end gap-1">
        {label}
        <ArrowUpDown className={`h-3 w-3 ${sortKey === key ? 'text-primary' : 'text-gray-600 group-hover:text-gray-400'}`} />
      </div>
    </th>
  );

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-400 uppercase bg-background/50 border-b border-border">
            <tr>
              <th className="px-4 py-3 font-medium cursor-pointer" onClick={() => handleSort('symbol')}>
                <div className="flex items-center gap-1">Company <ArrowUpDown className="h-3 w-3" /></div>
              </th>
              <SortHeader label="Mkt Cap" sortKey="market_cap" />
              <SortHeader label="P/E" sortKey="pe_ratio" />
              <SortHeader label="P/B" sortKey="pb_ratio" />
              <SortHeader label="ROE" sortKey="roe" />
              <SortHeader label="D/E" sortKey="debt_to_equity" />
              <SortHeader label="Rev Gr(Y/Y)" sortKey="revenue_growth" />
            </tr>
          </thead>
          <tbody>
            {sortedData.map((peer) => {
              const isCurrent = peer.symbol === currentSymbol;
              return (
                <tr 
                  key={peer.symbol} 
                  className={`border-b border-border/50 transition-colors ${isCurrent ? 'bg-primary/5 hover:bg-primary/10' : 'bg-card hover:bg-background/80'}`}
                >
                  <td className="px-4 py-4">
                    <Link href={`/stocks/${peer.symbol}`} className="block">
                      <div className={`font-semibold ${isCurrent ? 'text-primary' : 'text-foreground'} hover:underline`}>
                        {peer.symbol}
                      </div>
                      <div className="text-xs text-gray-400 truncate max-w-[150px]">{peer.name}</div>
                    </Link>
                  </td>
                  <td className="px-4 py-4 text-right font-medium">
                    {formatNumber(peer.market_cap, 'currency')}
                  </td>
                  <td className={`px-4 py-4 text-right ${getHighlightClass('pe_ratio', peer.pe_ratio, false)}`}>
                    {formatNumber(peer.pe_ratio)}
                  </td>
                  <td className={`px-4 py-4 text-right ${getHighlightClass('pb_ratio', peer.pb_ratio, false)}`}>
                    {formatNumber(peer.pb_ratio)}
                  </td>
                  <td className={`px-4 py-4 text-right ${getHighlightClass('roe', peer.roe, true)}`}>
                    {formatNumber(peer.roe, 'percent')}
                  </td>
                  <td className={`px-4 py-4 text-right ${getHighlightClass('debt_to_equity', peer.debt_to_equity, false)}`}>
                    {formatNumber(peer.debt_to_equity)}
                  </td>
                  <td className={`px-4 py-4 text-right ${getHighlightClass('revenue_growth', peer.revenue_growth, true)}`}>
                    {formatNumber(peer.revenue_growth, 'percent')}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="p-3 bg-background/30 text-xs text-gray-500 flex justify-between items-center border-t border-border">
        <span>Green indicates best among peers, Red indicates worst.</span>
        <span>Based on latest available fundamental data.</span>
      </div>
    </div>
  );
}

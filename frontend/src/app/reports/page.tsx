'use client';

import { useWatchlist } from '@/hooks/useStockData';
import Link from 'next/link';
import { FileText, ArrowRight, Search, FileSignature } from 'lucide-react';
import { useState } from 'react';

export default function ReportsList() {
  const { data: watchlist, isLoading } = useWatchlist();
  const [filter, setFilter] = useState('');

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-card rounded"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-40 bg-card rounded-lg border border-border"></div>
          ))}
        </div>
      </div>
    );
  }

  const filteredWatchlist = watchlist?.filter(item => 
    item.stock.symbol.toLowerCase().includes(filter.toLowerCase()) || 
    item.stock.name.toLowerCase().includes(filter.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-6 w-6 text-primary" />
          Research Reports
        </h1>
        
        <div className="relative w-full sm:w-64">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Filter stocks..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-card border border-border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
          />
        </div>
      </div>

      {!watchlist || watchlist.length === 0 ? (
        <div className="bg-card border border-border rounded-lg p-12 text-center shadow-sm">
          <FileSignature className="h-12 w-12 text-gray-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No stocks in watchlist</h3>
          <p className="text-gray-400 text-sm mb-6 max-w-md mx-auto">
            Add stocks to your watchlist to generate and manage automated research reports for them.
          </p>
          <Link href="/" className="text-primary hover:underline text-sm">
            Go to Dashboard
          </Link>
        </div>
      ) : filteredWatchlist.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          No stocks match your filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredWatchlist.map((item) => (
            <div key={item.id} className="bg-card border border-border rounded-lg p-6 shadow-sm hover:border-primary/50 transition-colors group flex flex-col h-full">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-lg text-primary">{item.stock.symbol}</h3>
                  <p className="text-xs text-gray-400 truncate max-w-[200px]" title={item.stock.name}>{item.stock.name}</p>
                </div>
                <div className={`px-2 py-0.5 rounded text-xs font-medium ${item.quote?.change && item.quote.change >= 0 ? 'bg-bullish/10 text-bullish' : 'bg-bearish/10 text-bearish'}`}>
                  {item.quote ? `${item.quote.change >= 0 ? '+' : ''}${item.quote.change_percent.toFixed(2)}%` : '-'}
                </div>
              </div>
              
              <div className="mt-auto pt-4 flex gap-2">
                <Link 
                  href={`/stocks/${item.stock.symbol}?tab=report`}
                  className="flex-1 text-center py-2 bg-primary/10 text-primary rounded text-sm font-medium hover:bg-primary hover:text-primary-foreground transition-colors"
                >
                  View Report
                </Link>
                <Link 
                  href={`/stocks/${item.stock.symbol}`}
                  className="px-3 py-2 bg-background border border-border text-foreground rounded flex items-center justify-center hover:bg-border transition-colors"
                  title="View full stock details"
                >
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

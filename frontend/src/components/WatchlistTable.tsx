'use client';

import { useWatchlist } from '@/hooks/useStockData';
import Link from 'next/link';
import FreshnessLabel from './FreshnessLabel';
import { TrendingUp, TrendingDown, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';

export default function WatchlistTable() {
  const { data: watchlist, isLoading, error, mutate } = useWatchlist();

  const handleRemove = async (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.removeFromWatchlist(id);
      mutate();
    } catch (err) {
      console.error('Failed to remove from watchlist', err);
    }
  };

  const formatNumber = (num: number | null) => {
    if (num === null) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  const formatVolume = (vol: number | null) => {
    if (vol === null) return '-';
    if (vol >= 10000000) return `${(vol / 10000000).toFixed(2)}Cr`;
    if (vol >= 100000) return `${(vol / 100000).toFixed(2)}L`;
    if (vol >= 1000) return `${(vol / 1000).toFixed(2)}K`;
    return vol.toString();
  };

  if (isLoading) {
    return (
      <div className="w-full bg-card border border-border rounded-lg overflow-hidden shadow-sm animate-pulse">
        <div className="h-12 bg-border/50 border-b border-border"></div>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="h-16 border-b border-border/50 bg-card"></div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-card border border-bearish/30 rounded-lg p-8 text-center">
        <p className="text-bearish">Failed to load watchlist.</p>
        <button onClick={() => mutate()} className="mt-2 text-sm text-primary hover:underline">Try again</button>
      </div>
    );
  }

  if (!watchlist || watchlist.length === 0) {
    return (
      <div className="w-full bg-card border border-border rounded-lg p-12 text-center shadow-sm">
        <div className="mx-auto w-16 h-16 bg-background rounded-full flex items-center justify-center mb-4">
          <TrendingUp className="h-8 w-8 text-gray-500" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">Your watchlist is empty</h3>
        <p className="text-sm text-gray-400 mb-6 max-w-md mx-auto">
          Keep track of your favorite stocks by adding them to your watchlist. Use the search bar above to find stocks.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full bg-card border border-border rounded-lg shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-400 uppercase bg-background/50 border-b border-border">
            <tr>
              <th scope="col" className="px-6 py-3 font-medium">Symbol / Name</th>
              <th scope="col" className="px-6 py-3 font-medium text-right">Price</th>
              <th scope="col" className="px-6 py-3 font-medium text-right">Change</th>
              <th scope="col" className="px-6 py-3 font-medium text-right hidden sm:table-cell">Volume</th>
              <th scope="col" className="px-6 py-3 font-medium text-center">Status</th>
              <th scope="col" className="px-6 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {watchlist.map((item) => {
              const quote = item.quote;
              const isPositive = quote && quote.change >= 0;
              
              return (
                <tr key={item.id} className="bg-card hover:bg-background/80 border-b border-border/50 transition-colors">
                  <td className="px-6 py-4">
                    <Link href={`/stocks/${item.stock.symbol}`} className="block">
                      <div className="font-semibold text-primary hover:underline">{item.stock.symbol}</div>
                      <div className="text-xs text-gray-400 truncate max-w-[200px]">{item.stock.name}</div>
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-right font-medium">
                    {formatNumber(quote?.price ?? null)}
                  </td>
                  <td className={`px-6 py-4 text-right font-medium ${isPositive ? 'text-bullish' : 'text-bearish'}`}>
                    {quote ? (
                      <div className="flex items-center justify-end gap-1">
                        {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        {quote.change > 0 ? '+' : ''}{quote.change.toFixed(2)} ({quote.change > 0 ? '+' : ''}{quote.change_percent.toFixed(2)}%)
                      </div>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 text-right text-gray-400 hidden sm:table-cell">
                    {formatVolume(quote?.volume ?? null)}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {quote && (
                      <FreshnessLabel 
                        data_quality={quote.data_quality} 
                        fetch_timestamp={quote.fetch_timestamp}
                        source_timestamp={quote.source_timestamp}
                      />
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={(e) => handleRemove(e, item.id)}
                      className="text-gray-500 hover:text-bearish transition-colors p-1"
                      title="Remove from watchlist"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

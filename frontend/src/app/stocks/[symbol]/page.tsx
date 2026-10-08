'use client';

import { useParams } from 'next/navigation';
import { useQuote, useCandles, useTechnical, useFundamentals, usePeers, useWatchlist } from '@/hooks/useStockData';
import { api } from '@/lib/api';
import useSWR from 'swr';
import { useState } from 'react';
import StockChart from '@/components/StockChart';
import TechnicalPanel from '@/components/TechnicalPanel';
import FundamentalsTable from '@/components/FundamentalsTable';
import PeerComparison from '@/components/PeerComparison';
import ResearchReportDisplay from '@/components/ResearchReport';
import FreshnessLabel from '@/components/FreshnessLabel';
import { TrendingUp, TrendingDown, RefreshCw, Star, BarChart2, Activity, FileSpreadsheet, Users, FileText } from 'lucide-react';

export default function StockDetail() {
  const params = useParams();
  const symbol = params.symbol as string;
  const [activeTab, setActiveTab] = useState<'chart' | 'technical' | 'fundamentals' | 'peers' | 'report'>('chart');
  const [chartPeriod, setChartPeriod] = useState('1y');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data: stock, isLoading: stockLoading } = useSWR(`stock-${symbol}`, () => api.getStock(symbol));
  const { data: quote, isLoading: quoteLoading, mutate: mutateQuote } = useQuote(symbol);
  const { data: candles, isLoading: candlesLoading } = useCandles(symbol, chartPeriod);
  const { data: technical, isLoading: technicalLoading } = useTechnical(activeTab === 'technical' ? symbol : null);
  const { data: fundamentals, isLoading: fundamentalsLoading } = useFundamentals(activeTab === 'fundamentals' ? symbol : null);
  const { data: peers, isLoading: peersLoading } = usePeers(activeTab === 'peers' ? symbol : null);
  const { data: report } = useSWR(activeTab === 'report' ? `report-latest-${symbol}` : null, () => api.getLatestReport(symbol));
  const { data: watchlist, mutate: mutateWatchlist } = useWatchlist();

  const isWatchlisted = watchlist?.some(item => item.stock.symbol === symbol);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await api.refreshStock(symbol);
      await mutateQuote();
    } catch (error) {
      console.error('Failed to refresh quote', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleWatchlistToggle = async () => {
    if (!stock) return;
    try {
      if (isWatchlisted) {
        const item = watchlist?.find(i => i.stock.symbol === symbol);
        if (item) await api.removeFromWatchlist(item.id);
      } else {
        await api.addToWatchlist(stock.id);
      }
      mutateWatchlist();
    } catch (error) {
      console.error('Failed to toggle watchlist', error);
    }
  };

  if (stockLoading) {
    return <div className="animate-pulse h-96 bg-card rounded-lg border border-border"></div>;
  }

  if (!stock) {
    return (
      <div className="bg-card border border-border rounded-lg p-12 text-center">
        <h2 className="text-xl font-bold mb-2">Stock Not Found</h2>
        <p className="text-gray-400">Could not find data for symbol: {symbol}</p>
      </div>
    );
  }

  const isPositive = quote && quote.change >= 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm sticky top-16 z-40">
        <div className="flex flex-col md:flex-row justify-between md:items-start gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">{stock.symbol}</h1>
              <span className="px-2 py-0.5 bg-border text-xs text-gray-300 rounded font-medium">{stock.exchange}</span>
              {stock.sector && <span className="text-xs text-primary hidden sm:inline-block">{stock.sector}</span>}
            </div>
            <p className="text-gray-400 text-sm">{stock.name}</p>
          </div>

          <div className="flex flex-col md:items-end">
            <div className="flex items-baseline gap-3 mb-1">
              {quoteLoading ? (
                <div className="h-8 w-24 bg-border/50 rounded animate-pulse"></div>
              ) : (
                <>
                  <span className="text-3xl font-bold">₹{quote?.price.toFixed(2)}</span>
                  <span className={`flex items-center text-sm font-semibold ${isPositive ? 'text-bullish' : 'text-bearish'}`}>
                    {isPositive ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                    {quote?.change > 0 ? '+' : ''}{quote?.change.toFixed(2)} ({quote?.change > 0 ? '+' : ''}{quote?.change_percent.toFixed(2)}%)
                  </span>
                </>
              )}
            </div>
            <div className="flex items-center gap-3 mt-2 md:mt-1">
              {quote && (
                <FreshnessLabel 
                  data_quality={quote.data_quality} 
                  fetch_timestamp={quote.fetch_timestamp} 
                  source_timestamp={quote.source_timestamp} 
                />
              )}
              <button 
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="text-gray-400 hover:text-primary transition-colors flex items-center gap-1 text-xs"
              >
                <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin text-primary' : ''}`} />
                Refresh
              </button>
              <button
                onClick={handleWatchlistToggle}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors ${
                  isWatchlisted ? 'bg-primary/20 text-primary hover:bg-primary/30' : 'bg-background hover:bg-border text-gray-300'
                }`}
              >
                <Star className={`h-3 w-3 ${isWatchlisted ? 'fill-primary text-primary' : ''}`} />
                {isWatchlisted ? 'Saved' : 'Watch'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border flex overflow-x-auto">
        {[
          { id: 'chart', label: 'Chart', icon: BarChart2 },
          { id: 'technical', label: 'Technical', icon: Activity },
          { id: 'fundamentals', label: 'Fundamentals', icon: FileSpreadsheet },
          { id: 'peers', label: 'Peers', icon: Users },
          { id: 'report', label: 'Report', icon: FileText },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-6 py-3 font-medium text-sm whitespace-nowrap transition-colors border-b-2 ${
              activeTab === tab.id 
                ? 'border-primary text-primary bg-primary/5' 
                : 'border-transparent text-gray-400 hover:text-foreground hover:bg-card'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="min-h-[500px]">
        {activeTab === 'chart' && (
          <StockChart 
            data={candles || []} 
            symbol={symbol} 
            period={chartPeriod} 
            onPeriodChange={setChartPeriod}
            isLoading={candlesLoading}
          />
        )}
        
        {activeTab === 'technical' && (
          <TechnicalPanel data={technical} isLoading={technicalLoading} />
        )}
        
        {activeTab === 'fundamentals' && (
          <FundamentalsTable data={fundamentals} isLoading={fundamentalsLoading} />
        )}

        {activeTab === 'peers' && (
          <PeerComparison data={peers} currentSymbol={symbol} isLoading={peersLoading} />
        )}

        {activeTab === 'report' && (
          <ResearchReportDisplay symbol={symbol} initialReport={report} />
        )}
      </div>
    </div>
  );
}

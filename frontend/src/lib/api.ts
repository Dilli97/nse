import {
  HealthStatus,
  Stock,
  WatchlistItem,
  Quote,
  Candle,
  TechnicalIndicator,
  FundamentalData,
  PeerData,
  ResearchReport
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Health
  health: () => fetchAPI<HealthStatus>('/api/health'),
  
  // Stocks
  searchStocks: (query: string) => fetchAPI<Stock[]>(`/api/stocks?search=${encodeURIComponent(query)}`),
  getStock: (symbol: string) => fetchAPI<Stock>(`/api/stocks/${symbol}`),
  
  // Watchlist
  getWatchlist: () => fetchAPI<WatchlistItem[]>('/api/watchlist'),
  addToWatchlist: (stockId: number) => fetchAPI<void>('/api/watchlist/items', { method: 'POST', body: JSON.stringify({ stock_id: stockId }) }),
  removeFromWatchlist: (itemId: number) => fetchAPI<void>(`/api/watchlist/items/${itemId}`, { method: 'DELETE' }),
  
  // Market Data
  getQuote: (symbol: string) => fetchAPI<Quote>(`/api/stocks/${symbol}/quote`),
  getCandles: (symbol: string, period?: string) => fetchAPI<Candle[]>(`/api/stocks/${symbol}/candles${period ? `?period=${period}` : ''}`),
  refreshStock: (symbol: string) => fetchAPI<void>(`/api/stocks/${symbol}/refresh`, { method: 'POST' }),
  
  // Analysis
  getTechnical: async (symbol: string): Promise<TechnicalIndicator[]> => {
    const res = await fetchAPI<any>(`/api/stocks/${symbol}/technical`);
    return Array.isArray(res) ? res : (res.indicators || []);
  },
  getFundamentals: (symbol: string) => fetchAPI<FundamentalData>(`/api/stocks/${symbol}/fundamentals`),
  getPeers: async (symbol: string): Promise<PeerData[]> => {
    const res = await fetchAPI<any>(`/api/stocks/${symbol}/peers`);
    return Array.isArray(res) ? res : (res.peers || []);
  },
  
  // Reports
  generateReport: (symbol: string) => fetchAPI<ResearchReport>(`/api/stocks/${symbol}/report`, { method: 'POST' }),
  getLatestReport: (symbol: string) => fetchAPI<ResearchReport>(`/api/stocks/${symbol}/report/latest`),
  
  // Settings
  getProviderStatus: () => fetchAPI<any>('/api/settings/providers'),
  importCSV: (formData: FormData) => fetch(`${API_BASE}/api/settings/import/csv`, { method: 'POST', body: formData }),
};

import useSWR from 'swr';
import { api } from '@/lib/api';

export function useWatchlist() {
  return useSWR('watchlist', api.getWatchlist, { refreshInterval: 30000 });
}

export function useQuote(symbol: string | null) {
  return useSWR(symbol ? `quote-${symbol}` : null, () => api.getQuote(symbol as string), { refreshInterval: 60000 });
}

export function useCandles(symbol: string | null, period?: string) {
  return useSWR(symbol ? `candles-${symbol}-${period || 'default'}` : null, () => api.getCandles(symbol as string, period));
}

export function useTechnical(symbol: string | null) {
  return useSWR(symbol ? `technical-${symbol}` : null, () => api.getTechnical(symbol as string));
}

export function useFundamentals(symbol: string | null) {
  return useSWR(symbol ? `fundamentals-${symbol}` : null, () => api.getFundamentals(symbol as string));
}

export function usePeers(symbol: string | null) {
  return useSWR(symbol ? `peers-${symbol}` : null, () => api.getPeers(symbol as string));
}

export function useHealth() {
  return useSWR('health', api.health, { refreshInterval: 60000 });
}

'use client';

import { useHealth } from '@/hooks/useStockData';
import { Database, Server, RefreshCw } from 'lucide-react';

export default function DataSourceStatus() {
  const { data: health, isLoading, error } = useHealth();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 animate-pulse">
        <div className="h-4 bg-border rounded w-1/3 mb-4"></div>
        <div className="h-3 bg-border rounded w-1/2 mb-2"></div>
        <div className="h-3 bg-border rounded w-2/3"></div>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="bg-card border border-bearish/30 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-bearish flex items-center gap-2 mb-2">
          <Server className="h-4 w-4" /> System Status Error
        </h3>
        <p className="text-xs text-gray-400">Could not connect to backend services.</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-4 shadow-sm">
      <h3 className="text-sm font-semibold flex items-center gap-2 border-b border-border pb-2">
        <Server className="h-4 w-4 text-primary" /> 
        System Status
      </h3>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center text-sm">
          <span className="flex items-center gap-2 text-gray-400">
            <Server className="h-3.5 w-3.5" /> API
          </span>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${health.status === 'ok' ? 'bg-bullish/10 text-bullish' : 'bg-bearish/10 text-bearish'}`}>
            {health.status.toUpperCase()}
          </span>
        </div>

        <div className="flex justify-between items-center text-sm">
          <span className="flex items-center gap-2 text-gray-400">
            <Database className="h-3.5 w-3.5" /> Database
          </span>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${health.database ? 'bg-bullish/10 text-bullish' : 'bg-bearish/10 text-bearish'}`}>
            {health.database ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
        </div>

        <div className="flex justify-between items-center text-sm">
          <span className="flex items-center gap-2 text-gray-400">
            <RefreshCw className="h-3.5 w-3.5" /> Provider
          </span>
          <div className="text-right">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${health.provider_status === 'ok' ? 'bg-bullish/10 text-bullish' : 'bg-neutral/10 text-neutral'}`}>
              {health.provider.toUpperCase()}
            </span>
          </div>
        </div>
      </div>
      
      <div className="pt-2 border-t border-border mt-2">
        <p className="text-[10px] text-gray-500 text-center">
          Last updated: {new Date(health.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

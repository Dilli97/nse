import WatchlistTable from '@/components/WatchlistTable';
import DataSourceStatus from '@/components/DataSourceStatus';
import Link from 'next/link';
import { Settings, FileText, Activity } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-6">
          <section>
            <div className="flex justify-between items-end mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                Your Watchlist
              </h2>
            </div>
            <WatchlistTable />
          </section>

          <section className="grid grid-cols-2 gap-4">
            <Link href="/reports" className="bg-card border border-border hover:border-primary/50 p-6 rounded-lg shadow-sm transition-colors group">
              <FileText className="h-6 w-6 text-primary mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-semibold mb-1">Research Reports</h3>
              <p className="text-sm text-gray-400">View generated analysis reports for your tracked stocks.</p>
            </Link>
            <Link href="/settings" className="bg-card border border-border hover:border-primary/50 p-6 rounded-lg shadow-sm transition-colors group">
              <Settings className="h-6 w-6 text-primary mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-semibold mb-1">Settings & Data</h3>
              <p className="text-sm text-gray-400">Configure data providers and import financial data.</p>
            </Link>
          </section>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <DataSourceStatus />
          
          <div className="bg-card border border-border rounded-lg p-5 shadow-sm">
            <h3 className="text-sm font-semibold mb-3">Market Status</h3>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm text-gray-400">NSE Equities</span>
              <span className="px-2 py-0.5 bg-bullish/10 text-bullish text-xs font-medium rounded">Open</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-gray-400">Data Delay</span>
              <span className="text-sm font-medium">15 mins</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

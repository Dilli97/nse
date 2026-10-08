'use client';

import Link from 'next/link';
import SearchBar from './SearchBar';
import { useHealth } from '@/hooks/useStockData';
import { Activity, Settings, BarChart2, Menu, X, FileText } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
  const { data: health } = useHealth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <nav className="bg-card border-b border-border sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center gap-2 text-primary font-bold text-xl tracking-tight">
            <Activity className="h-6 w-6" />
            <span>NSE Analysis</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center space-x-6">
            <SearchBar />
            
            <Link href="/" className="text-foreground hover:text-primary transition-colors flex items-center gap-1 text-sm font-medium">
              <BarChart2 className="h-4 w-4" />
              Dashboard
            </Link>
            
            <Link href="/reports" className="text-foreground hover:text-primary transition-colors flex items-center gap-1 text-sm font-medium">
              <FileText className="h-4 w-4" />
              Reports
            </Link>

            <Link href="/settings" className="text-foreground hover:text-primary transition-colors flex items-center gap-1 text-sm font-medium">
              <Settings className="h-4 w-4" />
              Settings
            </Link>

            {/* Health Indicator */}
            <div className="flex items-center gap-2" title={`System Status: ${health?.status || 'Unknown'}`}>
              <div className={`h-2.5 w-2.5 rounded-full ${health?.status === 'ok' ? 'bg-bullish animate-pulse' : 'bg-bearish'}`} />
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-foreground hover:text-primary"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-card border-t border-border p-4 space-y-4">
          <SearchBar />
          <div className="flex flex-col space-y-3">
            <Link href="/" onClick={() => setIsMobileMenuOpen(false)} className="text-foreground hover:text-primary flex items-center gap-2 text-sm">
              <BarChart2 className="h-4 w-4" />
              Dashboard
            </Link>
            <Link href="/reports" onClick={() => setIsMobileMenuOpen(false)} className="text-foreground hover:text-primary flex items-center gap-2 text-sm">
              <FileText className="h-4 w-4" />
              Reports
            </Link>
            <Link href="/settings" onClick={() => setIsMobileMenuOpen(false)} className="text-foreground hover:text-primary flex items-center gap-2 text-sm">
              <Settings className="h-4 w-4" />
              Settings
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

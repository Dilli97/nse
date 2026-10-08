export interface Stock {
  id: number;
  symbol: string;
  name: string;
  isin: string | null;
  exchange: string;
  sector: string | null;
  industry: string | null;
  is_active: boolean;
}

export interface Quote {
  stock_id: number;
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  open: number | null;
  high: number | null;
  low: number | null;
  prev_close: number | null;
  volume: number | null;
  market_cap: number | null;
  data_quality: 'live' | 'delayed' | 'eod' | 'stale' | 'demo';
  provider: string;
  source_timestamp: string | null;
  fetch_timestamp: string;
}

export interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface WatchlistItem {
  id: number;
  stock: Stock;
  quote: Quote | null;
}

export interface TechnicalIndicator {
  name: string;
  value: number | null;
  signal: 'bullish' | 'bearish' | 'neutral';
  description: string;
  timeframe: string;
  latest_candle_date: string;
  sufficient_data: boolean;
  periods_available: number;
  periods_required: number;
}

export interface FinancialRatio {
  name: string;
  value: number | null;
  period: string;
  period_type: string;
  is_meaningful: boolean;
  formula: string;
  unit: string;
}

export interface FundamentalData {
  ratios: FinancialRatio[];
  statements: any[];
  shareholding: any | null;
}

export interface PeerData {
  symbol: string;
  name: string;
  market_cap: number | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  revenue_growth: number | null;
}

export interface ResearchReport {
  id: number;
  stock_id: number;
  symbol: string;
  report_type: string;
  generated_at: string;
  generation_method: string;
  sections: ReportSection[];
  data_freshness: DataFreshness;
}

export interface ReportSection {
  title: string;
  content: string;
  data_points: any[];
}

export interface DataFreshness {
  quote_age_seconds: number | null;
  candle_last_date: string | null;
  fundamentals_last_date: string | null;
  overall_quality: string;
}

export interface HealthStatus {
  status: string;
  database: boolean;
  provider: string;
  provider_status: string;
  timestamp: string;
}

export interface AlertConfig {
  id: number;
  stock_id: number;
  symbol: string;
  alert_type: string;
  threshold: number;
  is_active: boolean;
  triggered_at: string | null;
}

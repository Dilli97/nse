'use client';

import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi } from 'lightweight-charts';
import { Candle } from '@/lib/types';
import FreshnessLabel from './FreshnessLabel';

interface StockChartProps {
  data: Candle[];
  symbol: string;
  period: string;
  onPeriodChange: (period: string) => void;
  isLoading?: boolean;
}

const PERIODS = [
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '3Y', value: '3y' },
  { label: '5Y', value: '5y' },
  { label: 'Max', value: 'max' },
];

export default function StockChart({ data, symbol, period, onPeriodChange, isLoading }: StockChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  
  const [legend, setLegend] = useState({ open: 0, high: 0, low: 0, close: 0, volume: 0, date: '' });

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8', // text-slate-400
      },
      grid: {
        vertLines: { color: '#334155' }, // border
        horzLines: { color: '#334155' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1, // Normal mode
      },
    });
    
    chartRef.current = chart;

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#10b981', // bullish
      downColor: '#ef4444', // bearish
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candlestickSeriesRef.current = candlestickSeries;

    const volumeSeries = chart.addHistogramSeries({
      color: '#3b82f6', // info
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // set as an overlay
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });
    volumeSeriesRef.current = volumeSeries;

    // Handle crosshair move for legend
    chart.subscribeCrosshairMove((param) => {
      if (param.time && param.seriesData.size > 0) {
        const candleData = param.seriesData.get(candlestickSeries) as any;
        const volData = param.seriesData.get(volumeSeries) as any;
        
        if (candleData) {
          setLegend({
            open: candleData.open,
            high: candleData.high,
            low: candleData.low,
            close: candleData.close,
            volume: volData ? volData.value : 0,
            date: typeof param.time === 'string' ? param.time : new Date((param.time as number) * 1000).toLocaleDateString(),
          });
        }
      }
    });

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || !data) return;

    const formattedData = data.map(d => ({
      time: d.date.split('T')[0], // yyyy-mm-dd
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    })).sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

    const volumeData = data.map(d => ({
      time: d.date.split('T')[0],
      value: d.volume,
      color: d.close >= d.open ? '#10b98180' : '#ef444480', // semi-transparent
    })).sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

    candlestickSeriesRef.current.setData(formattedData);
    volumeSeriesRef.current.setData(volumeData);
    
    if (chartRef.current && formattedData.length > 0) {
      chartRef.current.timeScale().fitContent();
      
      // Set initial legend
      const last = formattedData[formattedData.length - 1];
      const lastVol = volumeData[volumeData.length - 1];
      setLegend({
        open: last.open,
        high: last.high,
        low: last.low,
        close: last.close,
        volume: lastVol.value,
        date: last.time,
      });
    }
  }, [data]);

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm p-4 relative">
      {/* Header controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-4">
        <div>
          <h3 className="font-semibold text-lg">{symbol} Chart</h3>
          {legend.date && (
            <div className="text-xs flex gap-3 text-gray-400 mt-1 font-mono">
              <span>{legend.date}</span>
              <span>O: <span className="text-foreground">{legend.open.toFixed(2)}</span></span>
              <span>H: <span className="text-foreground">{legend.high.toFixed(2)}</span></span>
              <span>L: <span className="text-foreground">{legend.low.toFixed(2)}</span></span>
              <span>C: <span className="text-foreground">{legend.close.toFixed(2)}</span></span>
              <span>V: <span className="text-foreground">{(legend.volume / 1000).toFixed(1)}K</span></span>
            </div>
          )}
        </div>
        
        <div className="flex bg-background border border-border rounded-md p-0.5">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => onPeriodChange(p.value)}
              className={`px-2.5 py-1 text-xs font-medium rounded-sm transition-colors ${
                period === p.value 
                  ? 'bg-primary text-primary-foreground shadow-sm' 
                  : 'text-gray-400 hover:text-foreground hover:bg-card'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Container */}
      <div className="relative w-full h-[400px]">
        {isLoading && (
          <div className="absolute inset-0 z-10 bg-card/50 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}
        {!isLoading && (!data || data.length === 0) && (
          <div className="absolute inset-0 z-10 flex items-center justify-center text-gray-400">
            No chart data available for this period.
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>
      
      {/* Footer */}
      {data && data.length > 0 && (
        <div className="mt-2 text-right">
          <FreshnessLabel 
            data_quality="eod" 
            fetch_timestamp={data[0]?.date} 
          />
        </div>
      )}
    </div>
  );
}

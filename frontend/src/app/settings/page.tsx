'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import useSWR from 'swr';
import { Upload, FileSpreadsheet, Server, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import DataSourceStatus from '@/components/DataSourceStatus';

export default function Settings() {
  const { data: providers } = useSWR('/api/settings/providers', api.getProviderStatus);
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadStatus('idle');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await api.importCSV(formData);
      setUploadStatus('success');
      setUploadMessage('Data imported successfully');
      setFile(null);
    } catch (err: any) {
      setUploadStatus('error');
      setUploadMessage(err.message || 'Failed to import data');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold tracking-tight">Settings & Data Management</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* CSV Import Section */}
          <section className="bg-card border border-border rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <FileSpreadsheet className="h-5 w-5 text-primary" />
              Import Fundamental Data (CSV)
            </h2>
            <p className="text-sm text-gray-400 mb-6">
              Upload historical financial data, balance sheets, and income statements to enable fundamental analysis and peer comparison.
            </p>
            
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center bg-background/50 relative">
              <input 
                type="file" 
                accept=".csv" 
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={uploadStatus === 'uploading'}
              />
              <div className="flex flex-col items-center justify-center space-y-3">
                <Upload className="h-8 w-8 text-gray-400" />
                <div className="text-sm">
                  {file ? (
                    <span className="font-medium text-primary">{file.name}</span>
                  ) : (
                    <>
                      <span className="text-primary font-medium">Click to upload</span> or drag and drop
                    </>
                  )}
                </div>
                <p className="text-xs text-gray-500">CSV files only</p>
              </div>
            </div>

            {file && uploadStatus !== 'uploading' && uploadStatus !== 'success' && (
              <div className="mt-4 flex justify-end">
                <button 
                  onClick={handleUpload}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  Import Data
                </button>
              </div>
            )}

            {uploadStatus === 'uploading' && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-400">
                <RefreshCw className="h-4 w-4 animate-spin text-primary" /> Importing data...
              </div>
            )}

            {uploadStatus === 'success' && (
              <div className="mt-4 p-3 bg-bullish/10 border border-bullish/20 rounded flex items-start gap-2 text-bullish text-sm">
                <CheckCircle2 className="h-5 w-5 shrink-0" />
                <span>{uploadMessage}</span>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="mt-4 p-3 bg-bearish/10 border border-bearish/20 rounded flex items-start gap-2 text-bearish text-sm">
                <AlertCircle className="h-5 w-5 shrink-0" />
                <span>{uploadMessage}</span>
              </div>
            )}
          </section>

          {/* Provider Config Placeholder */}
          <section className="bg-card border border-border rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <Server className="h-5 w-5 text-primary" />
              Data Provider Configuration
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-background border border-border rounded-lg">
                <div>
                  <h3 className="font-medium">yfinance</h3>
                  <p className="text-xs text-gray-400">Default delayed market data provider</p>
                </div>
                <span className="px-2 py-1 bg-bullish/20 text-bullish text-xs rounded font-medium">Active</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-background border border-border rounded-lg opacity-60">
                <div>
                  <h3 className="font-medium">Zerodha Kite (Coming Soon)</h3>
                  <p className="text-xs text-gray-400">Live market data</p>
                </div>
                <span className="px-2 py-1 bg-border text-gray-400 text-xs rounded font-medium">Disabled</span>
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <DataSourceStatus />
        </div>
      </div>
    </div>
  );
}

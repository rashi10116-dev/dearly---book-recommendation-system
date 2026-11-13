import React, { useState, useEffect } from 'react';
import { X, Database, Upload, RefreshCw, CheckCircle2, AlertCircle, FileText, ArrowDownToLine, Sparkles } from 'lucide-react';
import { api } from '../api/client';

export default function DatasetManagerModal({ isOpen, onClose, onDatasetUpdated }) {
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadStats();
      setResult(null);
      setError('');
    }
  }, [isOpen]);

  const loadStats = async () => {
    setLoadingStats(true);
    try {
      const data = await api.dataset.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dataset stats:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV file to upload.');
      return;
    }
    setImporting(true);
    setError('');
    setResult(null);

    try {
      const importStats = await api.dataset.importCsv(file);
      setResult(importStats);
      await loadStats();
      if (onDatasetUpdated) onDatasetUpdated();
    } catch (err) {
      setError(err.message || 'CSV import failed.');
    } finally {
      setImporting(false);
    }
  };

  const handleResetSeed = async () => {
    if (!window.confirm('Reload the curated seed catalogue? Any newly added custom titles will be preserved or synced.')) return;
    setResetting(true);
    setError('');
    setResult(null);
    try {
      await api.dataset.resetSeed();
      await loadStats();
      if (onDatasetUpdated) onDatasetUpdated();
      alert('Seed catalogue reloaded and recommendation models re-fitted!');
    } catch (err) {
      setError(err.message || 'Seed reset failed.');
    } finally {
      setResetting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2A0F1D]/60 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-[#FCFAF6] border border-[#EAE3D9] rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh] relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full text-[#7A6E65] hover:text-[#2A0F1D] hover:bg-[#EAE3D9]/60 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="p-6 border-b border-[#EAE3D9] bg-white flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#571B37] text-white flex items-center justify-center">
            <Database className="w-5 h-5 text-[#E09E4B]" />
          </div>
          <div>
            <h2 className="font-editorial text-xl font-bold text-[#2A0F1D]">Dataset Management & Machine Learning</h2>
            <p className="text-xs text-[#7A6E65]">Import books from CSV, view catalog metrics, or re-fit recommendation models.</p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          
          {/* Catalog Metrics */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
                Books in Catalog
              </span>
              <span className="text-2xl font-bold font-editorial text-[#571B37]">
                {loadingStats ? '...' : stats?.total_books || 0}
              </span>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
                Active Genres
              </span>
              <span className="text-2xl font-bold font-editorial text-[#C48332]">
                {loadingStats ? '...' : stats?.total_genres || 0}
              </span>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
                ML Vector Space
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#E8EFEA] text-[#1C3829] inline-flex items-center gap-1 mt-1">
                <Sparkles className="w-3 h-3" />
                Active
              </span>
            </div>
          </div>

          {/* CSV File Upload Section */}
          <div className="bg-white p-5 rounded-2xl border border-[#EAE3D9] space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-editorial text-lg font-bold text-[#2A0F1D]">Import Custom Book CSV</h3>
                <p className="text-xs text-[#7A6E65]">Upload CSV containing columns: title, author, description, genre, tropes, etc.</p>
              </div>
              <a
                href="/backend/data/sample_books_dataset.csv"
                download="sample_books_template.csv"
                className="text-xs text-[#571B37] hover:underline flex items-center gap-1 font-semibold"
              >
                <ArrowDownToLine className="w-3.5 h-3.5" />
                Sample Template
              </a>
            </div>

            <form onSubmit={handleUpload} className="space-y-3">
              <div className="border-2 border-dashed border-[#D8CCC0] hover:border-[#571B37] rounded-2xl p-6 text-center cursor-pointer transition-colors bg-[#FAF7F2]">
                <input
                  type="file"
                  id="csv-file-input"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label htmlFor="csv-file-input" className="cursor-pointer block">
                  <Upload className="w-8 h-8 text-[#C48332] mx-auto mb-2" />
                  <p className="text-xs font-semibold text-[#2A0F1D]">
                    {file ? file.name : 'Click or drop a CSV file here'}
                  </p>
                  <p className="text-[11px] text-[#7A6E65] mt-0.5">Supports automatic column alias mapping & deduplication</p>
                </label>
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-[#FDF2F2] border border-[#F8B4B4] text-[#9B2C2C] text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {result && (
                <div className="p-4 rounded-xl bg-[#E8EFEA] border border-[#B7D8C5] text-[#1C3829] text-xs space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-[#2A533E]" />
                    Import Completed Successfully!
                  </div>
                  <p>Processed: {result.total_rows_processed} | Imported: {result.imported} | Updated: {result.updated} | Skipped: {result.skipped}</p>
                  <p>Total books in catalog: <strong>{result.total_books_in_catalog}</strong> (TF-IDF vector space re-fitted).</p>
                </div>
              )}

              <button
                type="submit"
                disabled={!file || importing}
                className="w-full py-2.5 rounded-xl bg-[#571B37] hover:bg-[#3D1426] text-white text-xs font-bold transition-all disabled:opacity-40 cursor-pointer"
              >
                {importing ? 'Processing & Re-indexing ML Engine...' : 'Import Dataset'}
              </button>
            </form>
          </div>

          {/* Reset Seed Database Option */}
          <div className="flex items-center justify-between p-4 rounded-2xl bg-[#EAE3D9]/40 border border-[#EAE3D9]">
            <div>
              <h4 className="text-xs font-bold text-[#2A0F1D]">Reload Seed Catalogue</h4>
              <p className="text-[11px] text-[#7A6E65]">Sync all 40 curated books and rebuild recommendation models.</p>
            </div>
            <button
              onClick={handleResetSeed}
              disabled={resetting}
              className="px-4 py-2 rounded-xl bg-white border border-[#EAE3D9] hover:border-[#571B37] text-xs font-semibold text-[#571B37] flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
              {resetting ? 'Syncing...' : 'Reload Seed'}
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}

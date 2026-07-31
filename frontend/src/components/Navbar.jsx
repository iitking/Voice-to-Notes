import React from 'react';
import { Mic, Sparkles, Database, Cpu, Activity, RefreshCw } from 'lucide-react';

export default function Navbar({ health, onRefreshHealth, isRefreshingHealth }) {
  const isHealthy = health?.status === 'healthy';
  const dbOk = health?.database === 'ok';
  const ollamaOk = health?.ollama?.status === 'ok';

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white shadow-sm shadow-teal-500/20">
            <Mic className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-slate-900 tracking-tight">VoiceToNotes</span>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                Local AI
              </span>
            </div>
            <p className="text-xs text-slate-500">faster-whisper • Ollama • PostgreSQL</p>
          </div>
        </div>

        {/* System Status Indicators */}
        <div className="hidden md:flex items-center gap-3">
          {/* Database pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <Database className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600">PostgreSQL:</span>
            <span className={`font-medium ${dbOk ? 'text-emerald-600' : 'text-amber-600'}`}>
              {dbOk ? 'Connected' : 'Connecting...'}
            </span>
          </div>

          {/* Whisper pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <Cpu className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600">Whisper:</span>
            <span className="font-medium text-emerald-600">{health?.whisper?.model || 'base'} (Local)</span>
          </div>

          {/* Ollama pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <Sparkles className="w-3.5 h-3.5 text-teal-500" />
            <span className="text-slate-600">LLM:</span>
            <span className={`font-medium ${ollamaOk ? 'text-emerald-600' : 'text-amber-600'}`}>
              {health?.ollama?.configured_model || 'qwen2.5:3b'}
            </span>
          </div>

          {/* Health check refresh */}
          <button
            onClick={onRefreshHealth}
            disabled={isRefreshingHealth}
            title="Refresh System Health"
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshingHealth ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
}

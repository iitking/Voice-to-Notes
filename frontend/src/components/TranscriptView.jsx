import React, { useState } from 'react';
import { Copy, Clock, Globe, AlignLeft } from 'lucide-react';

export default function TranscriptView({ transcript }) {
  const [copied, setCopied] = useState(false);

  if (!transcript) {
    return (
      <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 text-slate-400 text-sm">
        No transcript available for this audio yet.
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(transcript.full_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatSeconds = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = Math.floor(secs % 60);
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 space-y-6">
      {/* Header & Meta */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex flex-wrap items-center gap-2">
          {transcript.language && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-teal-50 text-teal-700 text-xs font-semibold border border-teal-200">
              <Globe className="w-3.5 h-3.5" />
              Language: {transcript.language.toUpperCase()}
              {transcript.language_probability && (
                <span className="text-teal-600 font-normal">
                  ({Math.round(transcript.language_probability * 100)}% prob)
                </span>
              )}
            </span>
          )}

          {transcript.duration_seconds && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-100 text-slate-700 text-xs font-medium">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              Duration: {transcript.duration_seconds.toFixed(1)}s
            </span>
          )}
        </div>

        <button
          onClick={handleCopy}
          className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-medium flex items-center gap-1.5 self-start sm:self-auto transition"
        >
          <Copy className="w-3.5 h-3.5" />
          {copied ? 'Copied Transcript!' : 'Copy Full Transcript'}
        </button>
      </div>

      {/* Full Transcript Paragraph */}
      <div>
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <AlignLeft className="w-3.5 h-3.5 text-teal-600" />
          Full Transcript
        </h4>
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-sm leading-relaxed text-slate-800 font-normal selection:bg-teal-100">
          {transcript.full_text}
        </div>
      </div>

      {/* Segment Timeline with Timestamps */}
      {transcript.segments && transcript.segments.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Timestamped Segments ({transcript.segments.length})
          </h4>
          <div className="space-y-2">
            {transcript.segments.map((seg, idx) => (
              <div
                key={seg.id || idx}
                className="p-3 rounded-xl bg-white border border-slate-100 hover:border-slate-200 transition flex items-start gap-3"
              >
                <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-mono text-[11px] font-medium flex-shrink-0 mt-0.5">
                  {formatSeconds(seg.start_seconds)} - {formatSeconds(seg.end_seconds)}
                </span>
                <p className="text-sm text-slate-700 leading-normal">{seg.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

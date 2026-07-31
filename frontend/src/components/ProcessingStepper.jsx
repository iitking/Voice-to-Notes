import React from 'react';
import { CheckCircle2, Clock, Loader2, AlertCircle, FileCheck, Cpu, Sparkles, AudioWaveform } from 'lucide-react';

const STAGES = [
  { id: 'validating', label: 'Audio Validation & FFmpeg Normalization', icon: AudioWaveform },
  { id: 'transcribing', label: 'Local faster-whisper Transcription', icon: Cpu },
  { id: 'generating_notes', label: 'Local Ollama Note Synthesis', icon: Sparkles },
  { id: 'completed', label: 'Completed & Stored in PostgreSQL', icon: FileCheck },
];

export default function ProcessingStepper({ job }) {
  if (!job) return null;

  const currentStatus = job.status; // 'queued' | 'validating' | 'transcribing' | 'generating_notes' | 'completed' | 'failed'
  const isFailed = currentStatus === 'failed';
  const isCompleted = currentStatus === 'completed';

  const getStageState = (stageId, index) => {
    if (isFailed) return 'error';
    if (isCompleted) return 'completed';

    const stageOrder = ['queued', 'validating', 'transcribing', 'generating_notes', 'completed'];
    const currentIndex = stageOrder.indexOf(currentStatus);
    const thisIndex = stageOrder.indexOf(stageId);

    if (thisIndex < currentIndex) return 'completed';
    if (thisIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            {isFailed ? 'Processing Failed' : isCompleted ? 'Processing Completed' : 'AI Processing Pipeline'}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {job.stage_message || 'Processing audio locally with faster-whisper and Ollama...'}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          {!isCompleted && !isFailed && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Processing
            </span>
          )}
          {isCompleted && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Ready
            </span>
          )}
          {isFailed && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
              <AlertCircle className="w-3.5 h-3.5" />
              Error
            </span>
          )}
        </div>
      </div>

      {/* Stepper Timeline */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2">
        {STAGES.map((stage, idx) => {
          const state = getStageState(stage.id, idx);
          const Icon = stage.icon;

          return (
            <div
              key={stage.id}
              className={`p-3.5 rounded-xl border transition flex flex-col justify-between ${
                state === 'completed'
                  ? 'bg-emerald-50/50 border-emerald-200 text-emerald-800'
                  : state === 'active'
                  ? 'bg-teal-50/70 border-teal-300 text-teal-900 ring-2 ring-teal-500/10'
                  : state === 'error'
                  ? 'bg-slate-50 border-slate-200 text-slate-400'
                  : 'bg-slate-50/60 border-slate-200/60 text-slate-400'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className={`w-5 h-5 ${state === 'completed' ? 'text-emerald-600' : state === 'active' ? 'text-teal-600' : 'text-slate-400'}`} />
                {state === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                {state === 'active' && <Loader2 className="w-4 h-4 text-teal-600 animate-spin" />}
                {state === 'pending' && <Clock className="w-4 h-4 text-slate-300" />}
              </div>
              <p className="text-xs font-semibold leading-tight line-clamp-2">
                {stage.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* Error Message Box */}
      {isFailed && (
        <div className="mt-4 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs">
          <div className="flex items-center gap-2 font-bold mb-1">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span>Error Code: {job.error_code || 'PROCESSING_ERROR'}</span>
          </div>
          <p>{job.error_message || 'An error occurred while processing the audio recording.'}</p>
        </div>
      )}
    </div>
  );
}

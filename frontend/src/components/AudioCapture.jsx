import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Upload, Play, Pause, RotateCcw, ArrowRight, Volume2, Globe, FileAudio } from 'lucide-react';

export default function AudioCapture({ onStartProcessing, isProcessing }) {
  const [mode, setMode] = useState('record'); // 'record' | 'upload'
  const [language, setLanguage] = useState('auto');
  
  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [micError, setMicError] = useState(null);

  // Upload state
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  const fileInputRef = useRef(null);

  // Timer effect
  useEffect(() => {
    if (isRecording && !isPaused) {
      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerIntervalRef.current);
    }
    return () => clearInterval(timerIntervalRef.current);
  }, [isRecording, isPaused]);

  // Clean audio URL on unmount or reset
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  const startRecording = async () => {
    setMicError(null);
    setRecordedBlob(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    setRecordingSeconds(0);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = MediaRecorder.isTypeSupported('audio/webm')
        ? { mimeType: 'audio/webm' }
        : {};
      const recorder = new MediaRecorder(stream, options);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const mimeType = recorder.mimeType || 'audio/webm';
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        setRecordedBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        // Stop audio tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start(250); // collect 250ms chunks
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setIsPaused(false);
    } catch (err) {
      console.error('Mic access error:', err);
      setMicError('Microphone access denied or not available. Please allow mic permissions in your browser.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
    }
  };

  const togglePause = () => {
    if (!mediaRecorderRef.current) return;
    if (isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
    } else {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
    }
  };

  const resetRecording = () => {
    setIsRecording(false);
    setIsPaused(false);
    setRecordingSeconds(0);
    setRecordedBlob(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    setMicError(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(URL.createObjectURL(file));
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('audio/')) {
      setUploadedFile(file);
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = () => {
    if (mode === 'record' && recordedBlob) {
      onStartProcessing(recordedBlob, 'voice_recording.webm', language);
    } else if (mode === 'upload' && uploadedFile) {
      onStartProcessing(uploadedFile, uploadedFile.name, language);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 overflow-hidden">
      {/* Top Header & Mode Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setMode('record'); resetRecording(); }}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-2 ${
              mode === 'record'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Mic className="w-4 h-4" />
            Record Voice
          </button>
          <button
            onClick={() => { setMode('upload'); resetRecording(); }}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-2 ${
              mode === 'upload'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload File
          </button>
        </div>

        {/* Language Selector */}
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-slate-400" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isRecording || isProcessing}
            className="text-xs font-medium bg-slate-50 border border-slate-200 text-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="auto">🌐 Auto-detect Language</option>
            <option value="en">English (en)</option>
            <option value="hi">Hindi (hi)</option>
            <option value="es">Spanish (es)</option>
            <option value="fr">French (fr)</option>
            <option value="de">German (de)</option>
          </select>
        </div>
      </div>

      {/* Mode 1: Record */}
      {mode === 'record' && (
        <div className="py-6 flex flex-col items-center text-center">
          {micError && (
            <div className="w-full mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl text-left">
              {micError}
            </div>
          )}

          {/* Pulsing Visualizer & Timer */}
          <div className="my-4 flex flex-col items-center">
            <div
              className={`w-28 h-28 rounded-full flex items-center justify-center transition-all ${
                isRecording
                  ? isPaused
                    ? 'bg-amber-100 text-amber-600 ring-4 ring-amber-200'
                    : 'bg-red-50 text-red-600 ring-8 ring-red-100 animate-pulse'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              <Mic className="w-12 h-12" />
            </div>

            <div className="mt-4 font-mono text-3xl font-bold text-slate-800 tracking-wider">
              {formatTime(recordingSeconds)}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {isRecording
                ? isPaused
                  ? 'Recording paused'
                  : 'Listening to microphone...'
                : recordedBlob
                ? 'Recording captured! Click Generate Notes below.'
                : 'Click Record to start speaking'}
            </p>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3 mt-4">
            {!isRecording ? (
              <button
                onClick={startRecording}
                disabled={isProcessing}
                className="px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm shadow-sm shadow-teal-600/30 flex items-center gap-2 transition disabled:opacity-50"
              >
                <Mic className="w-4 h-4" />
                {recordedBlob ? 'Record Again' : 'Start Recording'}
              </button>
            ) : (
              <>
                <button
                  onClick={togglePause}
                  className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-medium flex items-center gap-1.5 transition"
                >
                  {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                  {isPaused ? 'Resume' : 'Pause'}
                </button>
                <button
                  onClick={stopRecording}
                  className="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-sm font-semibold flex items-center gap-2 shadow-sm transition"
                >
                  <Square className="w-4 h-4 fill-current" />
                  Stop Recording
                </button>
              </>
            )}

            {recordedBlob && !isRecording && (
              <button
                onClick={resetRecording}
                className="p-3 rounded-xl border border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition"
                title="Discard recording"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Audio playback preview */}
          {audioUrl && !isRecording && (
            <div className="mt-6 w-full max-w-md bg-slate-50 p-3 rounded-xl border border-slate-200">
              <audio src={audioUrl} controls className="w-full h-8" />
            </div>
          )}
        </div>
      )}

      {/* Mode 2: Upload */}
      {mode === 'upload' && (
        <div className="py-6">
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*,.mp3,.wav,.m4a,.webm,.ogg,.aac,.flac"
            onChange={handleFileChange}
            className="hidden"
          />

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center ${
              dragActive
                ? 'border-teal-500 bg-teal-50/50'
                : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
            }`}
          >
            <div className="w-14 h-14 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mb-3">
              <Upload className="w-7 h-7" />
            </div>
            <p className="font-semibold text-slate-800 text-sm">
              Click to upload or drag and drop audio file
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Supports MP3, WAV, M4A, WEBM, OGG (Up to 100MB)
            </p>

            {uploadedFile && (
              <div className="mt-4 px-4 py-2 bg-white rounded-xl border border-slate-200 flex items-center gap-3 text-left">
                <FileAudio className="w-5 h-5 text-teal-600 flex-shrink-0" />
                <div className="overflow-hidden">
                  <p className="text-xs font-semibold text-slate-800 truncate">{uploadedFile.name}</p>
                  <p className="text-[11px] text-slate-500">{(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
              </div>
            )}
          </div>

          {audioUrl && (
            <div className="mt-4 bg-slate-50 p-3 rounded-xl border border-slate-200">
              <audio src={audioUrl} controls className="w-full h-8" />
            </div>
          )}
        </div>
      )}

      {/* Bottom Action Button */}
      {(recordedBlob || uploadedFile) && !isRecording && (
        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={handleSubmit}
            disabled={isProcessing}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50"
          >
            {isProcessing ? 'Processing Audio...' : 'Generate AI Notes'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

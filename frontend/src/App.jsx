import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import AudioCapture from './components/AudioCapture';
import ProcessingStepper from './components/ProcessingStepper';
import NotesView from './components/NotesView';
import TranscriptView from './components/TranscriptView';
import HistorySidebar from './components/HistorySidebar';
import {
  checkHealth,
  uploadAudio,
  getJobStatus,
  getTranscript,
  getNotes,
  getNote,
  deleteNote,
} from './services/api';
import { FileText, AlignLeft, Code2, Sparkles } from 'lucide-react';

export default function App() {
  // System Health
  const [health, setHealth] = useState(null);
  const [isRefreshingHealth, setIsRefreshingHealth] = useState(false);

  // Active Job & Processing State
  const [activeJob, setActiveJob] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Active Note & Transcript
  const [selectedNote, setSelectedNote] = useState(null);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [activeTab, setActiveTab] = useState('notes'); // 'notes' | 'transcript' | 'json'

  // History / Saved Notes
  const [notesList, setNotesList] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Polling ref
  const pollTimerRef = useRef(null);

  // Fetch initial health & notes
  const fetchHealthData = async () => {
    setIsRefreshingHealth(true);
    try {
      const data = await checkHealth();
      setHealth(data);
    } catch (err) {
      console.error('Health check failed:', err);
      setHealth({ status: 'unreachable', database: 'error', ollama: { status: 'error' } });
    } finally {
      setIsRefreshingHealth(false);
    }
  };

  const fetchNotesList = async (search = '') => {
    try {
      const list = await getNotes(search);
      setNotesList(list);
      // Auto select first note if none selected
      if (!selectedNote && list.length > 0) {
        handleSelectNote(list[0]);
      }
    } catch (err) {
      console.error('Failed to load notes list:', err);
    }
  };

  useEffect(() => {
    fetchHealthData();
    fetchNotesList();
    return () => clearInterval(pollTimerRef.current);
  }, []);

  // Poll active processing job until completed or failed
  const startJobPolling = (jobId) => {
    setIsProcessing(true);
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    pollTimerRef.current = setInterval(async () => {
      try {
        const job = await getJobStatus(jobId);
        setActiveJob(job);

        if (job.status === 'completed') {
          clearInterval(pollTimerRef.current);
          setIsProcessing(false);

          // Fetch the completed note and transcript
          if (job.note_id) {
            const freshNote = await getNote(job.note_id);
            setSelectedNote(freshNote);
          }
          if (job.transcript_id) {
            const freshTranscript = await getTranscript(job.transcript_id);
            setSelectedTranscript(freshTranscript);
          }
          // Refresh history list
          fetchNotesList();
          setActiveTab('notes');
        } else if (job.status === 'failed') {
          clearInterval(pollTimerRef.current);
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Error polling job status:', err);
      }
    }, 1500);
  };

  // Upload or record submit handler
  const handleStartProcessing = async (fileBlob, filename, language) => {
    try {
      const uploadRes = await uploadAudio(fileBlob, filename, language);
      setActiveJob({
        id: uploadRes.job_id,
        status: uploadRes.status,
        stage_message: 'Uploading recording and scheduling pipeline...',
      });
      startJobPolling(uploadRes.job_id);
    } catch (err) {
      alert(`Audio upload failed: ${err.message}`);
    }
  };

  const handleSelectNote = async (note) => {
    setSelectedNote(note);
    if (note.transcript_id) {
      try {
        const tr = await getTranscript(note.transcript_id);
        setSelectedTranscript(tr);
      } catch (e) {
        setSelectedTranscript(null);
      }
    } else {
      setSelectedTranscript(null);
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!window.confirm('Are you sure you want to delete this note?')) return;
    try {
      await deleteNote(noteId);
      const remaining = notesList.filter((n) => n.id !== noteId);
      setNotesList(remaining);
      if (selectedNote?.id === noteId) {
        setSelectedNote(remaining[0] || null);
        if (remaining[0]) {
          handleSelectNote(remaining[0]);
        } else {
          setSelectedTranscript(null);
        }
      }
    } catch (err) {
      alert(`Failed to delete note: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 selection:bg-teal-100 selection:text-teal-900">
      {/* Top Navigation */}
      <Navbar
        health={health}
        onRefreshHealth={fetchHealthData}
        isRefreshingHealth={isRefreshingHealth}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Voice to Structured Notes
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Transcribe spoken audio locally with faster-whisper and synthesize action items with Ollama.
          </p>
        </div>

        {/* 2-Column Responsive Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Studio & Viewer (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Audio Recording / Upload Studio */}
            <AudioCapture
              onStartProcessing={handleStartProcessing}
              isProcessing={isProcessing}
            />

            {/* Stepper (Visible during or immediately after processing) */}
            {activeJob && (
              <ProcessingStepper job={activeJob} />
            )}

            {/* Viewer Section with Tabs */}
            {selectedNote && (
              <div className="space-y-4">
                {/* Tabs */}
                <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
                  <button
                    onClick={() => setActiveTab('notes')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
                      activeTab === 'notes'
                        ? 'bg-teal-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Structured Notes
                  </button>

                  <button
                    onClick={() => setActiveTab('transcript')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
                      activeTab === 'transcript'
                        ? 'bg-teal-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <AlignLeft className="w-3.5 h-3.5" />
                    Full Transcript
                  </button>

                  <button
                    onClick={() => setActiveTab('json')}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${
                      activeTab === 'json'
                        ? 'bg-teal-600 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Code2 className="w-3.5 h-3.5" />
                    Raw JSON
                  </button>
                </div>

                {/* Tab 1: Notes View */}
                {activeTab === 'notes' && (
                  <NotesView
                    note={selectedNote}
                    transcript={selectedTranscript}
                    onNoteUpdated={(updated) => {
                      setSelectedNote(updated);
                      setNotesList((prev) =>
                        prev.map((n) => (n.id === updated.id ? updated : n))
                      );
                    }}
                    onNoteDeleted={handleDeleteNote}
                  />
                )}

                {/* Tab 2: Transcript View */}
                {activeTab === 'transcript' && (
                  <TranscriptView transcript={selectedTranscript} />
                )}

                {/* Tab 3: Raw JSON View */}
                {activeTab === 'json' && (
                  <div className="bg-slate-900 text-slate-100 rounded-2xl p-6 font-mono text-xs overflow-x-auto shadow-sm">
                    <pre>{JSON.stringify(selectedNote, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Column: History Sidebar (4 cols) */}
          <div className="lg:col-span-4 sticky top-24">
            <HistorySidebar
              notes={notesList}
              selectedNoteId={selectedNote?.id}
              onSelectNote={handleSelectNote}
              onDeleteNote={handleDeleteNote}
              searchQuery={searchQuery}
              onSearchChange={(query) => {
                setSearchQuery(query);
                fetchNotesList(query);
              }}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
          <p>
            Voice to Notes AI • 100% Local Inference with <span className="font-semibold text-slate-700">faster-whisper</span> & <span className="font-semibold text-slate-700">Ollama</span> • Saved in <span className="font-semibold text-slate-700">PostgreSQL</span>
          </p>
        </div>
      </footer>
    </div>
  );
}

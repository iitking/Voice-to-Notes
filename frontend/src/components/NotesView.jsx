import React, { useState } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  Circle,
  Tag,
  Clock,
  User,
  Trash2,
  Edit3,
  Check,
  X,
  Copy,
  Sparkles,
  RefreshCw,
  Share2,
} from 'lucide-react';
import { getExportUrl, toggleActionItem, updateNote, regenerateNotes } from '../services/api';

export default function NotesView({ note, transcript, onNoteUpdated, onNoteDeleted }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(note?.title || '');
  const [editedSummary, setEditedSummary] = useState(note?.summary || '');
  const [isSaving, setIsSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [customInstructions, setCustomInstructions] = useState('');
  const [showRegenModal, setShowRegenModal] = useState(false);

  if (!note) return null;

  const content = note.content_json || {};
  const keyPoints = content.key_points || [];
  const keywords = content.keywords || [];
  const actionItems = note.action_items || [];

  const handleToggleItem = async (itemId, currentCompleted) => {
    try {
      const updatedItem = await toggleActionItem(note.id, itemId, !currentCompleted);
      const updatedActionItems = actionItems.map((item) =>
        item.id === itemId ? { ...item, completed: updatedItem.completed } : item
      );
      onNoteUpdated({ ...note, action_items: updatedActionItems });
    } catch (err) {
      console.error('Failed to toggle action item:', err);
    }
  };

  const handleSaveEdit = async () => {
    setIsSaving(true);
    try {
      const updated = await updateNote(note.id, {
        title: editedTitle,
        summary: editedSummary,
      });
      onNoteUpdated(updated);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update note:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCopySummary = () => {
    navigator.clipboard.writeText(`${note.title}\n\n${note.summary}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = async () => {
    if (!note.transcript_id) return;
    setIsRegenerating(true);
    try {
      const regenerated = await regenerateNotes(note.transcript_id, customInstructions);
      onNoteUpdated(regenerated);
      setShowRegenModal(false);
      setCustomInstructions('');
    } catch (err) {
      alert(`Regeneration failed: ${err.message}`);
    } finally {
      setIsRegenerating(false);
    }
  };

  const formattedDate = new Date(note.created_at).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
      {/* Top Header / Actions */}
      <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50/50">
        <div className="flex-1">
          {isEditing ? (
            <input
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              className="w-full text-xl font-bold text-slate-900 bg-white border border-slate-300 rounded-xl px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          ) : (
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">{note.title}</h2>
          )}
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-2">
            <span>Created {formattedDate}</span>
            <span>•</span>
            <span className="text-teal-700 font-medium">Ollama Structured Output</span>
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSaveEdit}
                disabled={isSaving}
                className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold flex items-center gap-1.5 transition"
              >
                <Check className="w-3.5 h-3.5" />
                Save
              </button>
              <button
                onClick={() => {
                  setEditedTitle(note.title);
                  setEditedSummary(note.summary);
                  setIsEditing(false);
                }}
                className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-600 text-xs font-medium flex items-center gap-1.5 transition"
              >
                <X className="w-3.5 h-3.5" />
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-600 text-xs font-medium flex items-center gap-1.5 transition"
                title="Edit note text"
              >
                <Edit3 className="w-3.5 h-3.5" />
                Edit
              </button>

              <button
                onClick={() => setShowRegenModal(true)}
                className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-600 text-xs font-medium flex items-center gap-1.5 transition"
                title="Re-run Ollama LLM"
              >
                <RefreshCw className="w-3.5 h-3.5 text-teal-600" />
                Re-summarize
              </button>

              {/* Exports */}
              <a
                href={getExportUrl(note.id, 'md')}
                download
                className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
              >
                <Download className="w-3.5 h-3.5" />
                Markdown
              </a>
              <a
                href={getExportUrl(note.id, 'txt')}
                download
                className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-medium flex items-center gap-1.5 transition"
              >
                <Download className="w-3.5 h-3.5" />
                TXT
              </a>

              {/* Delete */}
              <button
                onClick={() => onNoteDeleted(note.id)}
                className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition"
                title="Delete Note"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Content Body */}
      <div className="p-6 space-y-6">
        {/* Executive Summary */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-600" />
              Executive Summary
            </h3>
            <button
              onClick={handleCopySummary}
              className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 transition"
            >
              <Copy className="w-3 h-3" />
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          {isEditing ? (
            <textarea
              rows={4}
              value={editedSummary}
              onChange={(e) => setEditedSummary(e.target.value)}
              className="w-full text-sm text-slate-700 bg-white border border-slate-300 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          ) : (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-sm leading-relaxed text-slate-700">
              {note.summary}
            </div>
          )}
        </div>

        {/* Key Points */}
        {keyPoints.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Key Points & Discussion Highlights
            </h3>
            <ul className="space-y-2">
              {keyPoints.map((point, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-xl bg-white border border-slate-100 text-sm text-slate-700 hover:border-slate-200 transition"
                >
                  <span className="w-5 h-5 rounded-full bg-teal-50 text-teal-700 font-semibold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                    {index + 1}
                  </span>
                  <span className="leading-normal">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Items */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Action Items ({actionItems.filter((i) => i.completed).length}/{actionItems.length})
            </h3>
          </div>

          {actionItems.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No explicit tasks or deadlines mentioned in this audio.</p>
          ) : (
            <div className="space-y-2">
              {actionItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleToggleItem(item.id, item.completed)}
                  className={`p-3 rounded-xl border cursor-pointer transition flex items-start justify-between gap-3 ${
                    item.completed
                      ? 'bg-emerald-50/40 border-emerald-200 text-slate-400 line-through'
                      : 'bg-white border-slate-200 text-slate-800 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <button className="mt-0.5 flex-shrink-0 text-slate-400 hover:text-emerald-600 transition">
                      {item.completed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <Circle className="w-4 h-4 text-slate-300" />
                      )}
                    </button>
                    <span className="text-sm font-medium leading-tight">{item.task}</span>
                  </div>

                  {/* Metadata (Owner / Deadline) */}
                  <div className="flex items-center gap-2 flex-shrink-0 no-underline">
                    {item.owner && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-[11px] font-medium">
                        <User className="w-3 h-3 text-slate-400" />
                        {item.owner}
                      </span>
                    )}
                    {item.deadline_text && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200 text-[11px] font-medium">
                        <Clock className="w-3 h-3 text-amber-500" />
                        {item.deadline_text}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Keywords */}
        {keywords.length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Keywords & Tags</h3>
            <div className="flex flex-wrap gap-2">
              {keywords.map((kw, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 text-xs font-medium border border-slate-200/60"
                >
                  #{kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Re-generate Modal */}
      {showRegenModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Re-summarize with Ollama</h3>
            <p className="text-xs text-slate-500 mb-4">
              You can provide optional custom instructions to guide the local LLM (e.g. "Focus on technical architecture" or "Keep it under 3 bullets").
            </p>
            <textarea
              rows={3}
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="E.g., Highlight action items specifically for next Monday..."
              className="w-full text-xs text-slate-700 border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-teal-500 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowRegenModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleRegenerate}
                disabled={isRegenerating}
                className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
              >
                {isRegenerating ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Run Ollama
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

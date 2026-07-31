import React from 'react';
import { Search, FileText, CheckCircle2, Trash2, Calendar, ChevronRight } from 'lucide-react';

export default function HistorySidebar({
  notes,
  selectedNoteId,
  onSelectNote,
  onDeleteNote,
  searchQuery,
  onSearchChange,
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-4 flex flex-col h-full max-h-[750px]">
      {/* Title & Search */}
      <div className="pb-3 border-b border-slate-100">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight mb-2">Saved Notes ({notes.length})</h3>
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search notes or summaries..."
            className="w-full text-xs pl-8 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>
      </div>

      {/* Notes List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 py-2">
        {notes.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            {searchQuery ? 'No matching notes found.' : 'No notes yet. Record or upload audio to start!'}
          </div>
        ) : (
          notes.map((note) => {
            const isSelected = note.id === selectedNoteId;
            const dateStr = new Date(note.created_at).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
            });
            const actionCount = note.action_items?.length || 0;

            return (
              <div
                key={note.id}
                onClick={() => onSelectNote(note)}
                className={`p-3 rounded-xl cursor-pointer transition flex items-start justify-between group my-1 ${
                  isSelected
                    ? 'bg-teal-50/70 border border-teal-200 shadow-xs'
                    : 'hover:bg-slate-50 border border-transparent'
                }`}
              >
                <div className="min-w-0 flex-1 mr-2">
                  <h4
                    className={`text-xs font-semibold truncate ${
                      isSelected ? 'text-teal-950 font-bold' : 'text-slate-800'
                    }`}
                  >
                    {note.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">{note.summary}</p>
                  <div className="flex items-center gap-2 mt-1.5 text-[10px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {dateStr}
                    </span>
                    {actionCount > 0 && (
                      <span className="flex items-center gap-1 text-emerald-600 font-medium">
                        <CheckCircle2 className="w-3 h-3" />
                        {actionCount} tasks
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteNote(note.id);
                    }}
                    className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                    title="Delete Note"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

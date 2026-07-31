const API_BASE = 'http://127.0.0.1:8000';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function uploadAudio(fileBlob, originalName = 'recording.wav', language = 'auto') {
  const formData = new FormData();
  formData.append('file', fileBlob, originalName);
  formData.append('language', language);

  const res = await fetch(`${API_BASE}/api/v1/audio`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail?.message || errorData.detail || 'Upload failed';
    throw new Error(message);
  }

  return res.json();
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
  if (!res.ok) throw new Error('Failed to fetch job status');
  return res.json();
}

export async function getTranscript(transcriptId) {
  const res = await fetch(`${API_BASE}/api/v1/transcripts/${transcriptId}`);
  if (!res.ok) throw new Error('Failed to fetch transcript');
  return res.json();
}

export async function getNotes(search = '') {
  const url = search ? `${API_BASE}/api/v1/notes?search=${encodeURIComponent(search)}` : `${API_BASE}/api/v1/notes`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch notes');
  return res.json();
}

export async function getNote(noteId) {
  const res = await fetch(`${API_BASE}/api/v1/notes/${noteId}`);
  if (!res.ok) throw new Error('Failed to fetch note');
  return res.json();
}

export async function updateNote(noteId, payload) {
  const res = await fetch(`${API_BASE}/api/v1/notes/${noteId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update note');
  return res.json();
}

export async function deleteNote(noteId) {
  const res = await fetch(`${API_BASE}/api/v1/notes/${noteId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete note');
  return res.json();
}

export async function toggleActionItem(noteId, itemId, completed) {
  const res = await fetch(`${API_BASE}/api/v1/notes/${noteId}/action-items/${itemId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed }),
  });
  if (!res.ok) throw new Error('Failed to update action item');
  return res.json();
}

export async function regenerateNotes(transcriptId, customInstructions = '') {
  const res = await fetch(`${API_BASE}/api/v1/notes/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transcript_id: transcriptId,
      custom_instructions: customInstructions || undefined,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || 'Failed to regenerate notes');
  }
  return res.json();
}

export function getExportUrl(noteId, format = 'md') {
  return `${API_BASE}/api/v1/notes/${noteId}/export?format=${format}`;
}

import { useState } from 'react';

export function AddNote() {
  const [text, setText] = useState('');
  const [status, setStatus] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('Saving…');
    const res = await fetch('http://localhost:8000/notes/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, category: 'note' }),
    });
    if (res.ok) {
      setStatus('saved');
      setText('');
    } else {
      setStatus('error saving');
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Type or paste your note…"
        rows={4}
      />
      <button type="submit">Add Note</button>
      {status && <p>{status}</p>}
    </form>
  );
}

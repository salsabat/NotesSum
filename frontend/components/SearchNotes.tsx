import { useState } from 'react';

export function SearchNotes() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<string[]>([]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(
      `http://localhost:8000/notes/search?query=${encodeURIComponent(query)}&top_k=5`
    );
    if (res.ok) {
      const json = await res.json();
      setResults(json.snippets);
    }
  }

  return (
    <div>
      <form onSubmit={handleSearch}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search your notes…"
        />
        <button type="submit">Search</button>
      </form>
      <ul>
        {results.map((snippet, i) => (
          <li key={i}>{snippet}</li>
        ))}
      </ul>
    </div>
  );
}

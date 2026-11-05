import { useMemo, useState } from 'react';
import { Briefcase, MapPin, Search, Send } from 'lucide-react';
import { Avatar, Modal, StatusChip } from './common.jsx';

// Composite, case-folded search vector from report section 3.3.
const vector = (p) => `${p.name} ${p.role} ${p.company} ${p.skills.join(' ')} ${p.degree}`.toLowerCase();

function PersonCard({ person, request, onRequest }) {
  // A declined request can be re-sent; pending/accepted ones are shown as status chips.
  const active = request && request.status !== 'declined' ? request : null;
  return (
    <article className="card person">
      <div className="person-head">
        <Avatar name={person.name} />
        <div>
          <h3>{person.name}</h3>
          <span className="mono">Class of {person.year} · {person.degree}</span>
        </div>
      </div>
      <p className="meta"><Briefcase size={14} /> {person.role} @ {person.company}</p>
      <p className="meta"><MapPin size={14} /> {person.location}</p>
      <p className="bio">{person.bio}</p>
      <div className="tags">{person.skills.map((s) => <span key={s} className="tag">{s}</span>)}</div>
      {active ? (
        <StatusChip status={active.status} />
      ) : (
        <button className="btn primary small" onClick={() => onRequest(person)}>
          <Send size={14} /> Request mentorship
        </button>
      )}
    </article>
  );
}

export default function Student({ people, requests, onSendRequest }) {
  const [query, setQuery] = useState('');
  const [target, setTarget] = useState(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const results = useMemo(() => {
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    return people.filter((p) => terms.every((t) => vector(p).includes(t)));
  }, [people, query]);

  // Latest request per alumnus, so a declined-then-resent request shows its newest status.
  const byAlumnus = useMemo(() => {
    const map = {};
    [...requests].reverse().forEach((r) => (map[r.alumni_profile_id] = r));
    return map;
  }, [requests]);

  async function send(e) {
    e.preventDefault();
    setBusy(true);
    const ok = await onSendRequest(target, message);
    setBusy(false);
    if (ok) {
      setTarget(null);
      setMessage('');
    }
  }

  return (
    <>
      <div className="searchbar">
        <Search size={18} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, role, company, degree or skill (try “python ai”)"
          aria-label="Search alumni"
        />
        <span className="mono">{results.length} / {people.length}</span>
      </div>
      <div className="people-grid">
        {results.map((p) => <PersonCard key={p.id} person={p} request={byAlumnus[p.id]} onRequest={setTarget} />)}
      </div>
      {results.length === 0 && <p className="empty">No alumni match “{query}”.</p>}

      {target && (
        <Modal title={`Request mentorship from ${target.name}`} onClose={() => setTarget(null)}>
          <form className="form" onSubmit={send}>
            <label>
              Message (optional)
              <textarea rows={4} maxLength={500} value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Introduce yourself and say what you'd like guidance on." />
            </label>
            <button className="btn primary" disabled={busy}>{busy ? 'Sending...' : 'Send request'}</button>
          </form>
        </Modal>
      )}
    </>
  );
}

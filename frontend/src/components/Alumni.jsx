import { useState } from 'react';
import { Check, Pencil, X } from 'lucide-react';
import { Avatar, StatusChip, formatWhen } from './common.jsx';
import { DirectoryModal } from './Faculty.jsx';

export default function Alumni({ user, people, requests, onSave, onResolve }) {
  const mine = people.find((p) => p.user_id === user.id) || null;
  const [editing, setEditing] = useState(false);
  const pending = requests.filter((r) => r.status === 'pending');
  const resolved = requests.filter((r) => r.status !== 'pending');

  return (
    <>
      <section className="card profile-card">
        {mine ? (
          <>
            <Avatar name={mine.name} size={60} />
            <div className="grow">
              <h3>{mine.name}</h3>
              <p className="meta">{mine.role} @ {mine.company} · {mine.location}</p>
              <div className="tags">{mine.skills.map((s) => <span key={s} className="tag">{s}</span>)}</div>
            </div>
            <button className="btn ghost" onClick={() => setEditing(true)}><Pencil size={15} /> Edit profile</button>
          </>
        ) : (
          <>
            <div className="grow">
              <h3>You are not in the directory yet</h3>
              <p className="muted">Create your profile so students can find and message you.</p>
            </div>
            <button className="btn primary" onClick={() => setEditing(true)}>Create profile</button>
          </>
        )}
      </section>

      <h2 className="section-title">Mentorship inbox <span className="count">{pending.length} pending</span></h2>
      {requests.length === 0 && <p className="empty">No mentorship requests yet.</p>}
      <div className="inbox">
        {pending.map((r) => (
          <article className="card request" key={r.id}>
            <Avatar name={r.student_name} />
            <div className="grow">
              <strong>{r.student_name}</strong>
              <small className="mono">{formatWhen(r.created_at)}</small>
              <p>{r.message || 'No message provided.'}</p>
            </div>
            <div className="row">
              <button className="btn primary small" onClick={() => onResolve(r, 'accepted')}><Check size={14} /> Accept</button>
              <button className="btn ghost small" onClick={() => onResolve(r, 'declined')}><X size={14} /> Decline</button>
            </div>
          </article>
        ))}
        {resolved.map((r) => (
          <article className="card request resolved" key={r.id}>
            <Avatar name={r.student_name} size={36} />
            <div className="grow">
              <strong>{r.student_name}</strong>
              <small className="mono">{formatWhen(r.updated_at)}</small>
            </div>
            <StatusChip status={r.status} />
          </article>
        ))}
      </div>

      {editing && (
        <DirectoryModal person={mine} onClose={() => setEditing(false)} onSave={(data) => onSave(mine?.id ?? null, data)} />
      )}
    </>
  );
}

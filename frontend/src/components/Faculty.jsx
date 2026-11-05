import { useState } from 'react';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { Avatar, Modal } from './common.jsx';

const EMPTY = { name: '', year: 2025, degree: '', role: '', company: '', location: '', skills: '', bio: '' };

// Shared by the Faculty console (any record) and the Alumni portal (own record).
export function DirectoryModal({ person, onClose, onSave }) {
  const [form, setForm] = useState(person ? { ...person, skills: person.skills.join(', ') } : EMPTY);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    const ok = await onSave({ ...form, year: Number(form.year) });
    setBusy(false);
    if (ok) onClose();
  }

  const field = (key, label, props = {}) => (
    <label>
      {label}
      <input required={key !== 'bio'} value={form[key]} onChange={set(key)} {...props} />
    </label>
  );

  return (
    <Modal title={person ? 'Edit alumni record' : 'Add alumni record'} onClose={onClose} wide>
      <form className="form grid2" onSubmit={submit}>
        {field('name', 'Full name')}
        {field('year', 'Graduation year', { type: 'number', min: 1980, max: 2035 })}
        {field('degree', 'Degree')}
        {field('role', 'Job title')}
        {field('company', 'Company')}
        {field('location', 'Location')}
        <label className="span2">
          Skills (comma separated)
          <input value={form.skills} onChange={set('skills')} placeholder="Python, Cloud, System Design" />
        </label>
        <label className="span2">
          Bio
          <textarea rows={3} value={form.bio} onChange={set('bio')} />
        </label>
        <button className="btn primary span2" disabled={busy}>{busy ? 'Saving...' : 'Save record'}</button>
      </form>
    </Modal>
  );
}

export default function Faculty({ people, requests, onSave, onDelete }) {
  const [editing, setEditing] = useState(null); // null | 'new' | person
  const [confirmId, setConfirmId] = useState(null);

  return (
    <>
      <div className="toolbar">
        <div className="stat"><strong>{people.length}</strong><span>Directory records</span></div>
        <div className="stat"><strong>{requests.filter((r) => r.status === 'pending').length}</strong><span>Pending requests</span></div>
        <button className="btn primary" onClick={() => setEditing('new')}><Plus size={16} /> Add alumnus</button>
      </div>

      <div className="directory-list">
        {people.map((p) => (
          <div className="directory-row" key={p.id}>
            <Avatar name={p.name} size={36} />
            <div className="grow">
              <strong>{p.name}</strong>
              <small>{p.role} @ {p.company}</small>
            </div>
            <span className="mono hide-sm">{p.year} · {p.degree}</span>
            <div className="row">
              <button className="icon-btn" aria-label={`Edit ${p.name}`} onClick={() => setEditing(p)}><Pencil size={16} /></button>
              {confirmId === p.id ? (
                <>
                  <button className="btn danger small" onClick={() => { onDelete(p); setConfirmId(null); }}>Confirm delete</button>
                  <button className="btn ghost small" onClick={() => setConfirmId(null)}>Cancel</button>
                </>
              ) : (
                <button className="icon-btn" aria-label={`Delete ${p.name}`} onClick={() => setConfirmId(p.id)}><Trash2 size={16} /></button>
              )}
            </div>
          </div>
        ))}
      </div>

      {editing && (
        <DirectoryModal
          person={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSave={(data) => onSave(editing === 'new' ? null : editing.id, data)}
        />
      )}
    </>
  );
}

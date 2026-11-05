import { useRef, useState } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, Clock3, MapPin, Plus, Trash2, Upload } from 'lucide-react';
import { Modal, formatWhen } from './common.jsx';

const KINDS = ['Community', 'Workshop', 'Talk', 'Networking', 'Reunion'];
const MAX_POSTER_BYTES = 1_536_000;
const POSTER_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export function EventsCarousel({ events, onOpen, onCreate }) {
  const track = useRef(null);
  const scroll = (dir) => track.current?.scrollBy({ left: dir * 320, behavior: 'smooth' });

  return (
    <section className="events">
      <div className="section-head">
        <h2 className="section-title"><CalendarDays size={20} /> Upcoming events</h2>
        <div className="row">
          <button className="icon-btn" onClick={() => scroll(-1)} aria-label="Scroll left"><ChevronLeft size={18} /></button>
          <button className="icon-btn" onClick={() => scroll(1)} aria-label="Scroll right"><ChevronRight size={18} /></button>
          <button className="btn primary small" onClick={onCreate}><Plus size={14} /> New event</button>
        </div>
      </div>
      {events.length === 0 ? (
        <p className="empty">No upcoming events. Be the first to create one.</p>
      ) : (
        <div className="carousel" ref={track}>
          {events.map((e) => (
            <button key={e.id} className="event-card" onClick={() => onOpen(e)}>
              <div className="poster" style={e.poster_url ? { backgroundImage: `url(${e.poster_url})` } : undefined}>
                {!e.poster_url && <CalendarDays size={32} />}
                <span className="chip kind">{e.kind}</span>
              </div>
              <h3>{e.title}</h3>
              <p className="meta"><Clock3 size={13} /> {formatWhen(e.starts_at)}</p>
              <p className="meta"><MapPin size={13} /> {e.location}</p>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

export function EventDetail({ event, user, onClose, onRsvp, onDelete }) {
  const canDelete = user.role === 'faculty' || event.creator_id === user.id;
  return (
    <Modal title={event.title} onClose={onClose} wide>
      {event.poster_url && <img className="detail-poster" src={event.poster_url} alt={`${event.title} poster`} />}
      <p className="meta"><Clock3 size={14} /> {formatWhen(event.starts_at)} to {formatWhen(event.ends_at)}</p>
      <p className="meta"><MapPin size={14} /> {event.location}</p>
      <p className="meta"><span className="chip kind">{event.kind}</span> Hosted by {event.creator_name}</p>
      <p>{event.description || 'No description provided.'}</p>
      <div className="row">
        <button className={`btn ${event.going ? 'ghost' : 'primary'}`} onClick={() => onRsvp(event)}>
          {event.going ? 'Cancel RSVP' : 'RSVP'}
        </button>
        <span className="muted">{event.rsvp_count} going</span>
        {canDelete && (
          <button className="btn danger small push-right" onClick={() => onDelete(event)}><Trash2 size={14} /> Delete</button>
        )}
      </div>
    </Modal>
  );
}

export function EventForm({ onClose, onSubmit, onError }) {
  const [form, setForm] = useState({ title: '', starts_at: '', ends_at: '', location: '', kind: 'Community', description: '' });
  const [poster, setPoster] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  function pick(e) {
    const file = e.target.files[0];
    if (!file) return setPoster(null);
    // Same limits the FastAPI service enforces; checking here just gives instant feedback.
    if (!POSTER_TYPES.includes(file.type)) {
      onError('Poster must be a JPEG, PNG or WebP image.');
      e.target.value = '';
      return;
    }
    if (file.size > MAX_POSTER_BYTES) {
      onError('Poster must be 1.5 MB or smaller.');
      e.target.value = '';
      return;
    }
    setPoster(file);
  }

  async function submit(e) {
    e.preventDefault();
    if (new Date(form.ends_at) <= new Date(form.starts_at)) return onError('The end time must be after the start time.');
    const data = new FormData();
    Object.entries(form).forEach(([k, v]) => data.append(k, v));
    if (poster) data.append('poster', poster);
    setBusy(true);
    const ok = await onSubmit(data);
    setBusy(false);
    if (ok) onClose();
  }

  return (
    <Modal title="Create an event" onClose={onClose} wide>
      <form className="form grid2" onSubmit={submit}>
        <label className="span2">
          Title
          <input required maxLength={80} value={form.title} onChange={set('title')} />
        </label>
        <label>
          Starts
          <input type="datetime-local" required value={form.starts_at} onChange={set('starts_at')} />
        </label>
        <label>
          Ends
          <input type="datetime-local" required value={form.ends_at} onChange={set('ends_at')} />
        </label>
        <label>
          Location
          <input required value={form.location} onChange={set('location')} />
        </label>
        <label>
          Category
          <select value={form.kind} onChange={set('kind')}>{KINDS.map((k) => <option key={k}>{k}</option>)}</select>
        </label>
        <label className="span2">
          Description
          <textarea rows={3} maxLength={500} value={form.description} onChange={set('description')} />
        </label>
        <label className="span2 upload">
          <Upload size={16} /> {poster ? poster.name : 'Poster image (JPEG, PNG or WebP, up to 1.5 MB)'}
          <input type="file" accept={POSTER_TYPES.join(',')} onChange={pick} hidden />
        </label>
        <button className="btn primary span2" disabled={busy}>{busy ? 'Publishing...' : 'Publish event'}</button>
      </form>
    </Modal>
  );
}

import { CheckCheck, X } from 'lucide-react';
import { formatWhen } from './common.jsx';

export default function Notifications({ notices, onClose, onRead, onReadAll }) {
  return (
    <div className="backdrop drawer-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="drawer" role="dialog" aria-label="Notifications">
        <header>
          <h2>Notifications</h2>
          <div className="row">
            <button className="btn ghost small" onClick={onReadAll}><CheckCheck size={14} /> Mark all read</button>
            <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button>
          </div>
        </header>
        {notices.length === 0 && <p className="empty">You're all caught up.</p>}
        <ul>
          {notices.map((n) => (
            <li key={n.id} className={n.read ? 'read' : 'unread'}>
              <button onClick={() => !n.read && onRead(n)}>
                <span>{n.message}</span>
                <small className="mono">{formatWhen(n.created_at)}</small>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}

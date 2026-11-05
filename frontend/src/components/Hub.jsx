import { Bell, GraduationCap, HeartHandshake, LogOut, Users, Lock, ArrowRight } from 'lucide-react';
import { Avatar } from './common.jsx';

export function Topbar({ user, unread, onBell, onLogout, onHome }) {
  return (
    <header className="topbar">
      <button className="brand" onClick={onHome}>
        <GraduationCap size={22} /> Alumni Connect
      </button>
      <div className="topbar-right">
        {user ? (
          <>
            <button className="icon-btn bell" onClick={onBell} aria-label={`Notifications, ${unread} unread`}>
              <Bell size={19} />
              {unread > 0 && <span className="badge">{unread}</span>}
            </button>
            <div className="who">
              <Avatar name={user.name} size={32} />
              <span>
                {user.name}
                <small>{user.role}</small>
              </span>
            </div>
            <button className="icon-btn" onClick={onLogout} aria-label="Sign out">
              <LogOut size={18} />
            </button>
          </>
        ) : null}
      </div>
    </header>
  );
}

export function Landing({ onAuth }) {
  return (
    <section className="landing">
      <div className="wave wave-a" />
      <div className="wave wave-b" />
      <div className="wave wave-c" />
      <div className="ambient-glow" />
      <div className="landing-copy">
        <p className="eyebrow">Students · Faculty · Alumni</p>
        <h1>
          Your Community.
          <br />
          Your Next Chapter.
        </h1>
        <p className="lead">Great things start together. Find mentors, shape the network, and show up for your community.</p>
        <div className="row">
          <button className="btn primary" onClick={() => onAuth('signup')}>
            Create account <ArrowRight size={16} />
          </button>
          <button className="btn ghost" onClick={() => onAuth('login')}>
            Sign in
          </button>
        </div>
      </div>
    </section>
  );
}

const PORTALS = [
  { role: 'student', no: '01', title: 'Student Portal', tag: 'Explore Your Path', icon: Users, blurb: 'Search alumni by skill, company or degree and request mentorship in one click.' },
  { role: 'faculty', no: '02', title: 'Faculty Portal', tag: 'Shape the Network', icon: GraduationCap, blurb: 'Curate the alumni directory: add, edit and remove records.' },
  { role: 'alumni', no: '03', title: 'Alumni Portal', tag: 'Pay It Forward', icon: HeartHandshake, blurb: 'Keep your profile current and answer mentorship requests.' },
];

export function PortalHub({ user, onEnter, children }) {
  return (
    <main className="page">
      <h1 className="page-title">Welcome, {user.name.split(' ')[0]}</h1>
      <p className="muted">Choose a workspace. Portals unlock according to your account role.</p>
      <div className="portal-grid">
        {PORTALS.map((p) => {
          const allowed = p.role === user.role;
          return (
            <button key={p.role} className={`portal-card ${allowed ? '' : 'locked'}`} disabled={!allowed} onClick={() => onEnter(p.role)}>
              <span className="mono role-no">{p.no}</span>
              <p.icon size={28} />
              <h3>{p.title}</h3>
              <strong>{p.tag}</strong>
              <p>{p.blurb}</p>
              <span className="portal-cta">
                {allowed ? <>Enter <ArrowRight size={14} /></> : <><Lock size={14} /> {p.role} account required</>}
              </span>
            </button>
          );
        })}
      </div>
      {children}
    </main>
  );
}

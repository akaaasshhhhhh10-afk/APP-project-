import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { api, loadSession, saveSession } from './api.js';
import { Toasts } from './components/common.jsx';
import AuthModal from './components/AuthModal.jsx';
import { Landing, PortalHub, Topbar } from './components/Hub.jsx';
import Student from './components/Student.jsx';
import Faculty from './components/Faculty.jsx';
import Alumni from './components/Alumni.jsx';
import { EventDetail, EventForm, EventsCarousel } from './components/Events.jsx';
import Notifications from './components/Notifications.jsx';

const PORTAL_TITLES = {
  student: ['Student Portal', 'Find a mentor and request guidance.'],
  faculty: ['Faculty Portal', 'Curate the alumni directory.'],
  alumni: ['Alumni Portal', 'Manage your profile and mentorship requests.'],
};
const POLL_MS = 30_000;

export default function App() {
  const [user, setUser] = useState(() => loadSession()?.user ?? null);
  const [portal, setPortal] = useState(null); // null = hub
  const [people, setPeople] = useState([]);
  const [events, setEvents] = useState([]);
  const [requests, setRequests] = useState([]);
  const [notices, setNotices] = useState([]);
  const [authMode, setAuthMode] = useState(null);
  const [eventForm, setEventForm] = useState(false);
  const [eventDetail, setEventDetail] = useState(null);
  const [drawer, setDrawer] = useState(false);
  const [toasts, setToasts] = useState([]);

  const toast = useCallback((text, kind = 'ok') => {
    const id = Math.random();
    setToasts((t) => [...t, { id, text, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  const logout = useCallback(() => {
    saveSession(null);
    setUser(null);
    setPortal(null);
    setPeople([]);
    setEvents([]);
    setRequests([]);
    setNotices([]);
  }, []);

  // Wraps API calls: expired sessions sign the user out, anything else becomes a toast.
  const guarded = useCallback(
    async (fn) => {
      try {
        return await fn();
      } catch (err) {
        if (err.status === 401) {
          logout();
          toast('Your session expired. Please sign in again.', 'error');
        } else {
          toast(err.message, 'error');
        }
        return undefined;
      }
    },
    [logout, toast],
  );

  const refreshLive = useCallback(
    () =>
      Promise.all([api.requests(), api.notifications(), api.events()]).then(([r, n, e]) => {
        setRequests(r);
        setNotices(n);
        setEvents(e);
      }),
    [],
  );

  // Hydrate everything in parallel after sign-in (report: Promise.all hydration).
  useEffect(() => {
    if (!user) return undefined;
    guarded(async () => {
      const [p] = await Promise.all([api.alumni(), refreshLive()]);
      setPeople(p);
    });
    const timer = setInterval(() => guarded(refreshLive), POLL_MS);
    return () => clearInterval(timer);
  }, [user, guarded, refreshLive]);

  const unread = useMemo(() => notices.filter((n) => !n.read).length, [notices]);

  function onSession(session) {
    saveSession(session);
    setUser(session.user);
    setAuthMode(null);
    toast(`Signed in as ${session.user.name}`);
  }

  async function signOut() {
    await api.logout().catch(() => {});
    logout();
  }

  // ---- directory
  const savePerson = (id, data) =>
    guarded(async () => {
      const saved = id ? await api.updateAlumnus(id, data) : await api.createAlumnus(data);
      setPeople((list) => (id ? list.map((p) => (p.id === id ? saved : p)) : [saved, ...list]));
      toast(id ? 'Record updated' : 'Record added');
      return true;
    }).then(Boolean);

  const deletePerson = (person) =>
    guarded(async () => {
      await api.deleteAlumnus(person.id);
      setPeople((list) => list.filter((p) => p.id !== person.id));
      toast(`${person.name} removed from the directory`);
    });

  // ---- mentorship
  const sendRequest = (person, message) =>
    guarded(async () => {
      const created = await api.requestMentorship(person.id, message);
      setRequests((list) => [created, ...list]);
      setNotices(await api.notifications());
      toast(`Request sent to ${person.name}`);
      return true;
    }).then(Boolean);

  const resolveRequest = (req, status) =>
    guarded(async () => {
      const updated = await api.resolveRequest(req.id, status);
      setRequests((list) => list.map((r) => (r.id === req.id ? updated : r)));
      toast(`Request ${status}`);
    });

  // ---- events
  const createEvent = (form) =>
    guarded(async () => {
      await api.createEvent(form);
      setEvents(await api.events());
      toast('Event published');
      return true;
    }).then(Boolean);

  const toggleRsvp = (event) =>
    guarded(async () => {
      const { going, rsvp_count } = await api.rsvp(event.id);
      const patch = (e) => (e.id === event.id ? { ...e, going, rsvp_count } : e);
      setEvents((list) => list.map(patch));
      setEventDetail((e) => (e ? patch(e) : e));
      toast(going ? 'You are going!' : 'RSVP cancelled');
    });

  const deleteEvent = (event) =>
    guarded(async () => {
      await api.deleteEvent(event.id);
      setEvents((list) => list.filter((e) => e.id !== event.id));
      setEventDetail(null);
      toast('Event deleted');
    });

  // ---- notifications
  const markRead = (n) =>
    guarded(async () => {
      await api.markRead(n.id);
      setNotices((list) => list.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
    });

  const markAllRead = () =>
    guarded(async () => {
      await api.markAllRead();
      setNotices((list) => list.map((x) => ({ ...x, read: true })));
    });

  function renderPortal() {
    switch (portal) {
      case 'student':
        return <Student people={people} requests={requests} onSendRequest={sendRequest} />;
      case 'faculty':
        return <Faculty people={people} requests={requests} onSave={savePerson} onDelete={deletePerson} />;
      default:
        return <Alumni user={user} people={people} requests={requests} onSave={savePerson} onResolve={resolveRequest} />;
    }
  }

  const eventsSection = (
    <EventsCarousel events={events} onOpen={setEventDetail} onCreate={() => setEventForm(true)} />
  );

  return (
    <div className="app-shell">
      <Topbar user={user} unread={unread} onBell={() => setDrawer(true)} onLogout={signOut} onHome={() => setPortal(null)} />

      {!user && <Landing onAuth={setAuthMode} />}

      {user && !portal && (
        <PortalHub user={user} onEnter={setPortal}>
          {eventsSection}
        </PortalHub>
      )}

      {user && portal && (
        <main className="page">
          <button className="link back" onClick={() => setPortal(null)}>
            <ArrowLeft size={15} /> All portals
          </button>
          <h1 className="page-title">{PORTAL_TITLES[portal][0]}</h1>
          <p className="muted">{PORTAL_TITLES[portal][1]}</p>
          {renderPortal()}
          {eventsSection}
        </main>
      )}

      {/* Modals are top-level siblings so stacking contexts never clip them. */}
      {authMode && <AuthModal initialMode={authMode} onClose={() => setAuthMode(null)} onSession={onSession} />}
      {eventForm && <EventForm onClose={() => setEventForm(false)} onSubmit={createEvent} onError={(m) => toast(m, 'error')} />}
      {eventDetail && (
        <EventDetail event={eventDetail} user={user} onClose={() => setEventDetail(null)} onRsvp={toggleRsvp} onDelete={deleteEvent} />
      )}
      {drawer && <Notifications notices={notices} onClose={() => setDrawer(false)} onRead={markRead} onReadAll={markAllRead} />}
      <Toasts toasts={toasts} />
    </div>
  );
}

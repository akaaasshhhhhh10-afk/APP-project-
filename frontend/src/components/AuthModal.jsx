import { useState } from 'react';
import { Modal } from './common.jsx';
import { api } from '../api.js';

const DEMOS = [
  ['Student', 'student@demo.com'],
  ['Faculty', 'faculty@demo.com'],
  ['Alumni', 'alumni@demo.com'],
];

export default function AuthModal({ initialMode, onClose, onSession }) {
  const [mode, setMode] = useState(initialMode);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const session = mode === 'signup' ? await api.signup(form) : await api.login(form);
      onSession(session);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={mode === 'signup' ? 'Create your account' : 'Welcome back'} onClose={onClose}>
      <form onSubmit={submit} className="form">
        {mode === 'signup' && (
          <>
            <label>
              Full name
              <input value={form.name} onChange={set('name')} placeholder="Leave blank to use your email prefix" />
            </label>
            <label>
              I am a
              <select value={form.role} onChange={set('role')}>
                <option value="student">Student</option>
                <option value="faculty">Faculty member</option>
                <option value="alumni">Alumnus</option>
              </select>
            </label>
          </>
        )}
        <label>
          Email
          <input type="email" required value={form.email} onChange={set('email')} autoComplete="email" />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            minLength={8}
            value={form.password}
            onChange={set('password')}
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
          />
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="btn primary" disabled={busy}>
          {busy ? 'Please wait...' : mode === 'signup' ? 'Create account' : 'Sign in'}
        </button>
        <p className="muted center">
          {mode === 'signup' ? 'Already a member?' : 'New here?'}{' '}
          <button type="button" className="link" onClick={() => setMode(mode === 'signup' ? 'login' : 'signup')}>
            {mode === 'signup' ? 'Sign in' : 'Create an account'}
          </button>
        </p>
        {mode === 'login' && (
          <div className="demo-box">
            <span className="muted">Demo accounts (password: password123)</span>
            <div className="row">
              {DEMOS.map(([label, email]) => (
                <button type="button" key={email} className="btn ghost small" onClick={() => setForm({ ...form, email, password: 'password123' })}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}
      </form>
    </Modal>
  );
}

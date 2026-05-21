import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../components/Toast.jsx';

export function Login() {
  const { login, register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), password);
      }
      navigate('/', { replace: true });
    } catch (err) {
      toast.error(err.message || 'Đăng nhập thất bại');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-bg" />
      <div className="auth-card">
        <div className="auth-brand">
          <div className="logo">⚽</div>
          <div>
            <h1>Prediction League</h1>
            <div className="auth-sub">World Cup 2026 — sảnh cá cược nội bộ</div>
          </div>
        </div>

        <div className="tabs" style={{ marginBottom: 22 }}>
          <button
            className={`tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => setMode('login')}
          >
            Đăng nhập
          </button>
          <button
            className={`tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => setMode('register')}
          >
            Đăng ký
          </button>
        </div>

        <form className="auth-form" onSubmit={submit}>
          <label className="field">
            <span>Tên đăng nhập</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              minLength={3}
            />
          </label>
          <label className="field">
            <span>Mật khẩu</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              minLength={6}
            />
          </label>
          <button className="btn btn-primary btn-block" disabled={busy}>
            {busy ? 'Đang xử lý…' : mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}
          </button>
        </form>

        <div className="auth-hint">
          Tài khoản quản trị do hệ thống khởi tạo sẵn.
        </div>
      </div>
    </div>
  );
}

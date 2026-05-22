import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { GroupSelector } from './GroupSelector.jsx';

const NAV = [
  { to: '/', icon: '🏆', label: 'Bảng xếp hạng', exact: true },
  { to: '/matches', icon: '⚽', label: 'Trận đấu', exact: false },
  { to: '/admin', icon: '⚙️', label: 'Admin', exact: false, adminOnly: true },
];

function titleFor(pathname) {
  if (pathname === '/') return 'Bảng xếp hạng';
  if (pathname.startsWith('/matches/')) return 'Chi tiết trận';
  if (pathname.startsWith('/matches')) return 'Trận đấu';
  if (pathname.startsWith('/players/')) return 'Chi tiết người chơi';
  if (pathname.startsWith('/admin/groups/')) return 'Cài đặt group';
  if (pathname.startsWith('/admin')) return 'Admin Console';
  return 'World Cup 2026';
}

export function Layout() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const initials = (user?.display_name || '?').slice(0, 2).toUpperCase();

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="logo sm">⚽</div>
          <div className="brand-text">
            <strong>Prediction</strong>
            World Cup 2026
          </div>
        </div>
        <nav className="nav">
          {NAV.filter((n) => !n.adminOnly || user?.is_admin).map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.exact}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="ni">{n.icon}</span>
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="main">
        <header className="topbar">
          <h2>{titleFor(pathname)}</h2>
          <div className="topbar-right">
            <GroupSelector />
            <div className="user-chip">
              <div className="avatar">{initials}</div>
              <div className="user-meta">
                <strong>{user?.display_name}</strong>
                <small>{user?.is_admin ? 'Quản trị viên' : 'Người chơi'}</small>
              </div>
            </div>
            <button
              className="btn btn-ghost btn-sm"
              onClick={logout}
              title="Đăng xuất"
            >
              Đăng xuất
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

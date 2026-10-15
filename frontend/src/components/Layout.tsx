import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Layout() {
  const { user, signOut } = useAuth();

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="app-header__logo">
          <div className="app-header__logo-icon">🌻</div>
          <span>Sahara</span>
        </div>
        <nav className="app-header__nav">
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
            {user?.displayName || user?.email}
          </span>
          <button className="btn btn--ghost" onClick={signOut} style={{ fontSize: 'var(--text-sm)' }}>
            Sign Out
          </button>
        </nav>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="bottom-nav" aria-label="Main navigation">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
          }
        >
          <span className="bottom-nav__icon">🏠</span>
          <span>Home</span>
        </NavLink>
        <NavLink
          to="/chat"
          className={({ isActive }) =>
            `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
          }
        >
          <span className="bottom-nav__icon">💬</span>
          <span>Talk</span>
        </NavLink>
        <NavLink
          to="/reminders"
          className={({ isActive }) =>
            `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
          }
        >
          <span className="bottom-nav__icon">⏰</span>
          <span>Reminders</span>
        </NavLink>
        <NavLink
          to="/checkin"
          className={({ isActive }) =>
            `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
          }
        >
          <span className="bottom-nav__icon">💚</span>
          <span>Check-in</span>
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`
          }
        >
          <span className="bottom-nav__icon">⚙️</span>
          <span>Settings</span>
        </NavLink>
      </nav>
    </div>
  );
}

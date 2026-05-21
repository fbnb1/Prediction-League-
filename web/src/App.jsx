import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';
import { GroupProvider } from './context/GroupContext.jsx';
import { ToastProvider } from './components/Toast.jsx';
import { Layout } from './components/Layout.jsx';
import { Login } from './pages/Login.jsx';
import { Home } from './pages/Home.jsx';
import { Matches } from './pages/Matches.jsx';
import { MatchDetail } from './pages/MatchDetail.jsx';
import { PlayerDetail } from './pages/PlayerDetail.jsx';
import { Admin } from './pages/Admin.jsx';
import { GroupSettings } from './pages/GroupSettings.jsx';

function AuthedShell() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return (
    <GroupProvider>
      <Layout />
    </GroupProvider>
  );
}

function RequireAdmin({ children }) {
  const { user } = useAuth();
  if (!user?.is_admin) return <Navigate to="/" replace />;
  return children;
}

function LoginRoute() {
  const { user } = useAuth();
  if (user) return <Navigate to="/" replace />;
  return <Login />;
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            <Route element={<AuthedShell />}>
              <Route index element={<Home />} />
              <Route path="matches" element={<Matches />} />
              <Route path="matches/:matchId" element={<MatchDetail />} />
              <Route path="players/:userId" element={<PlayerDetail />} />
              <Route
                path="admin"
                element={
                  <RequireAdmin>
                    <Admin />
                  </RequireAdmin>
                }
              />
              <Route
                path="admin/groups/:groupId"
                element={
                  <RequireAdmin>
                    <GroupSettings />
                  </RequireAdmin>
                }
              />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

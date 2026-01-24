import React from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import { LogOut, User } from 'lucide-react';
import UserPortal from './components/UserPortal';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Landing from './pages/Landing';
import BorrowerFunnel from './pages/BorrowerFunnel';
import ApplicantDashboard from './pages/ApplicantDashboard';
import ManagerDashboard from './pages/ManagerDashboard';
import ApplicationDetail from './pages/ApplicationDetail';
import { AuthProvider, useAuth } from './context/AuthContext';
import RequireAuth from './components/RequireAuth';

function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  // Minimal navbar for landing and funnel pages
  const isPublicPage = ['/', '/funnel'].includes(location.pathname);

  return (
    <nav className={`${isPublicPage && !user ? 'bg-transparent absolute w-full z-10' : 'bg-gray-800'} text-white p-4`}>
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <Link to={user ? '/dashboard' : '/'} className="text-xl font-bold flex items-center gap-2 hover:opacity-90 transition">
          <span>🏦</span>
          <span className="hidden sm:inline">Moxi Mortgage</span>
        </Link>

        {user ? (
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center text-sm text-gray-300 gap-2">
              <User size={16} /> {user.email} <span className="text-xs bg-gray-700 px-1 rounded">{user.role}</span>
            </div>
            <div className="space-x-4 flex items-center">
              <Link to="/dashboard" className="hover:text-blue-300 transition text-sm">Dashboard</Link>
              {user.role === 'manager' && (
                <Link to="/manager" className="hover:text-blue-300 transition text-sm">Manager View</Link>
              )}
              <button onClick={logout} className="bg-gray-700 hover:bg-red-600 p-2 rounded-full transition" title="Logout">
                <LogOut size={16} />
              </button>
            </div>
          </div>
        ) : (
          <div className="space-x-4 text-sm">
            <Link to="/login" className={`hover:text-blue-300 transition ${isPublicPage ? 'text-gray-700' : ''}`}>Login</Link>
            <Link to="/funnel" className={`px-4 py-2 rounded-lg transition font-medium ${isPublicPage ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-blue-600 hover:bg-blue-700'}`}>
              Get Started
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen">
          <NavBar />
          <main className="bg-gray-50 min-h-[calc(100vh-64px)]">
            <Routes>
              {/* Public Routes - Moxi Portal */}
              <Route path="/" element={<Landing />} />
              <Route path="/funnel" element={<BorrowerFunnel />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected Routes */}
              <Route path="/dashboard" element={
                <RequireAuth>
                  <ApplicantDashboard />
                </RequireAuth>
              } />
              <Route path="/apply" element={
                <RequireAuth>
                  <UserPortal />
                </RequireAuth>
              } />
              <Route path="/manager" element={
                <RequireAuth>
                  <ManagerDashboard />
                </RequireAuth>
              } />
              <Route path="/manager/application/:id" element={
                <RequireAuth>
                  <ApplicationDetail />
                </RequireAuth>
              } />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
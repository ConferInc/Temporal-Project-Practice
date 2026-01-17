import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import UserPortal from './components/UserPortal';
import ManagerDashboard from './components/ManagerDashboard';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <nav className="bg-gray-800 text-white p-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="text-xl font-bold">🏦 Moxi Mortgage Auto-Underwriter</div>
            <div className="space-x-4">
              <Link to="/" className="hover:text-blue-300 transition">User Application</Link>
              <Link to="/manager" className="hover:text-blue-300 transition">Manager Dashboard</Link>
            </div>
          </div>
        </nav>

        <main className="bg-gray-50 min-h-[calc(100vh-64px)]">
          <Routes>
            <Route path="/" element={<UserPortal />} />
            <Route path="/manager" element={<ManagerDashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
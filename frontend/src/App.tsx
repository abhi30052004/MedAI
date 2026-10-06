import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';
import Cases from './pages/Cases';
import CaseDetail from './pages/CaseDetail';

import Team from './pages/Team';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="patients" element={<div className="p-4 bg-white rounded-xl shadow-sm border border-gray-100 h-[60vh] flex items-center justify-center text-gray-500">Patients Module Coming Soon</div>} />
          <Route path="cases" element={<Cases />} />
          <Route path="cases/:id" element={<CaseDetail />} />
          <Route path="documents" element={<div className="p-4 bg-white rounded-xl shadow-sm border border-gray-100 h-[60vh] flex items-center justify-center text-gray-500">Documents Module Coming Soon</div>} />
          <Route path="analysis" element={<div className="p-4 bg-white rounded-xl shadow-sm border border-gray-100 h-[60vh] flex items-center justify-center text-gray-500">AI Analysis Module Coming Soon</div>} />
          <Route path="team" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Team />
            </ProtectedRoute>
          } />
          <Route path="*" element={<div className="p-4 bg-white rounded-xl shadow-sm border border-gray-100 h-[60vh] flex items-center justify-center text-gray-500">Page Not Found</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;


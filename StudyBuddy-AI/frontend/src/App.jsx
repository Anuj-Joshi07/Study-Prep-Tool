import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

// Shared
import Landing from './pages/Landing'
import Login from './pages/Login'
import Layout from './components/Layout'

// School / JEE platform
import JEEPlatform from './pages/JEEPlatform'

// Engineering / StudyBuddy pages
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Quiz from './pages/Quiz'
import Resume from './pages/Resume'
import Roadmap from './pages/Roadmap'
import Interview from './pages/Interview'
import Documents from './pages/Documents'

function RequireAuth({ children }) {
  return localStorage.getItem('student_id') ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing — choose your path */}
        <Route path="/" element={<Landing />} />

        {/* Auth */}
        <Route path="/login" element={<Login />} />

        {/* School / JEE Platform — no auth required */}
        <Route path="/jee" element={<JEEPlatform />} />

        {/* Engineering / StudyBuddy — requires login */}
        <Route path="/dashboard" element={<RequireAuth><Layout><Dashboard /></Layout></RequireAuth>} />
        <Route path="/chat"      element={<RequireAuth><Layout><Chat /></Layout></RequireAuth>} />
        <Route path="/quiz"      element={<RequireAuth><Layout><Quiz /></Layout></RequireAuth>} />
        <Route path="/resume"    element={<RequireAuth><Layout><Resume /></Layout></RequireAuth>} />
        <Route path="/roadmap"   element={<RequireAuth><Layout><Roadmap /></Layout></RequireAuth>} />
        <Route path="/interview" element={<RequireAuth><Layout><Interview /></Layout></RequireAuth>} />
        <Route path="/documents" element={<RequireAuth><Layout><Documents /></Layout></RequireAuth>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

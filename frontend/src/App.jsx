import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import ComingSoon from './components/ComingSoon'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="lg:pl-64">
        <Header onMenuClick={() => setMenuOpen(true)} />
        <main className="p-4 sm:p-8 max-w-6xl">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/study" element={<ComingSoon title="Study Mode" needs="the Study backend and an API key (Phase 4)" />} />
            <Route path="/research" element={<ComingSoon title="Research Mode" needs="the Research backend (Phase 4)" />} />
            <Route path="/viva" element={<ComingSoon title="Viva Mode" needs="the Viva backend (Phase 4)" />} />
            <Route path="/qa" element={<ComingSoon title="Document Q&A" needs="document retrieval (Phases 3-4)" />} />
            <Route path="/evaluation" element={<ComingSoon title="Prompt Evaluation" needs="the evaluation backend (Phase 5)" />} />
            <Route path="/lab" element={<ComingSoon title="Prompt Engineering Lab" needs="the Prompt Lab backend (Phase 5)" />} />
            <Route path="*" element={<ComingSoon title="This page" needs="a valid address" />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import ComingSoon from './components/ComingSoon'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import StudyMode from './pages/StudyMode'
import DocumentQA from './pages/DocumentQA'
import ResearchMode from './pages/ResearchMode'
import VivaMode from './pages/VivaMode'

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
            <Route path="/study" element={<StudyMode />} />
            <Route path="/research" element={<ResearchMode />} />
            <Route path="/viva" element={<VivaMode />} />
            <Route path="/qa" element={<DocumentQA />} />
            <Route path="/evaluation" element={<ComingSoon title="Prompt Evaluation" needs="the evaluation backend (Phase 5)" />} />
            <Route path="/lab" element={<ComingSoon title="Prompt Engineering Lab" needs="the Prompt Lab backend (Phase 5)" />} />
            <Route path="*" element={<ComingSoon title="This page" needs="a valid address" />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
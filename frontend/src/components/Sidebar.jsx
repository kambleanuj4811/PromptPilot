import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, FileText, GraduationCap, Microscope,
  Mic, MessageSquare, Scale, FlaskConical, X,
} from 'lucide-react'

export const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/study', label: 'Study Mode', icon: GraduationCap },
  { to: '/research', label: 'Research Mode', icon: Microscope },
  { to: '/viva', label: 'Viva Mode', icon: Mic },
  { to: '/qa', label: 'Document Q&A', icon: MessageSquare },
  { to: '/evaluation', label: 'Prompt Evaluation', icon: Scale },
  { to: '/lab', label: 'Prompt Engineering Lab', icon: FlaskConical },
]

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={onClose} aria-hidden="true" />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 text-slate-300 flex flex-col
        transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex items-center justify-between px-5 h-16 border-b border-slate-800">
          <span className="text-lg font-semibold text-white">
            Prompt<span className="text-indigo-400">Pilot</span>
          </span>
          <button onClick={onClose} className="lg:hidden text-slate-400 hover:text-white" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <p className="px-5 py-4 text-xs text-slate-500 border-t border-slate-800">
          AI grading and evaluation are estimates.
        </p>
      </aside>
    </>
  )
}
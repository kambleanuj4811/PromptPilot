import { useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { NAV_ITEMS } from './Sidebar'

export default function Header({ onMenuClick }) {
  const { pathname } = useLocation()
  const current = NAV_ITEMS.find((i) => i.to === pathname)

  return (
    <header className="sticky top-0 z-20 flex items-center gap-3 h-16 px-4 sm:px-8 bg-white/90 backdrop-blur border-b border-slate-200">
      <button onClick={onMenuClick} className="lg:hidden text-slate-600" aria-label="Open menu">
        <Menu size={22} />
      </button>
      <h1 className="text-lg font-semibold text-slate-800">{current ? current.label : 'PromptPilot'}</h1>
    </header>
  )
}
import { Loader2 } from 'lucide-react'

export default function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 py-6" role="status">
      <Loader2 className="animate-spin" size={18} />
      <span className="text-sm">{message}</span>
    </div>
  )
}
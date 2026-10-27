import { AlertCircle } from 'lucide-react'

export default function ErrorMessage({ message }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
      <AlertCircle size={18} className="mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  )
}
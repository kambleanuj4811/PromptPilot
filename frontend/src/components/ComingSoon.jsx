import { Construction } from 'lucide-react'

export default function ComingSoon({ title, needs }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <Construction className="mx-auto text-slate-400" size={32} />
      <h2 className="mt-3 text-lg font-semibold text-slate-800">{title} is not built yet</h2>
      <p className="mt-1 text-sm text-slate-500">
        Waiting for: {needs}. This page will use real backend data once that is done.
      </p>
    </div>
  )
}
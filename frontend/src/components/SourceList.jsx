import { FileText } from 'lucide-react'

export default function SourceList({ sources }) {
  if (!sources?.length) return null
  return (
    <section className="mt-6">
      <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Retrieved passages</h3>
      <ul className="mt-2 space-y-2">
        {sources.map((s) => (
          <li
            key={s.id}
            className={`rounded-lg border p-3 text-xs ${
              s.cited ? 'border-green-300 bg-green-50' : 'border-slate-200 bg-slate-50'
            }`}
          >
            <p className="flex items-center gap-1 font-medium text-slate-700">
              <FileText size={14} /> {s.filename}, page {s.page_number}
              {s.cited && <span className="ml-2 rounded bg-green-200 px-1.5 text-green-800">cited</span>}
            </p>
            <p className="mt-1 text-slate-600">{s.snippet}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
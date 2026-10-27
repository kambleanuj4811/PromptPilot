import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStats, getActivity } from '../api/dashboard'
import client, { errorMessage } from '../api/client'
import LoadingState from '../components/LoadingState'
import ErrorMessage from '../components/ErrorMessage'
import { NAV_ITEMS } from '../components/Sidebar'
import { formatTime } from '../utils/time'

const DESCRIPTIONS = {
  '/documents': 'Upload and manage PDFs',
  '/study': 'Explain, summarize, MCQs, revision notes',
  '/research': 'Structured paper analysis',
  '/viva': 'Practice oral exam questions',
  '/qa': 'Ask questions grounded in your documents',
  '/evaluation': 'Compare Prompt A vs Prompt B',
  '/lab': 'See prompting techniques run live',
}

const ACTIVITY_LABELS = {
  document_upload: 'Document',
  document_qa: 'Q&A',
  study: 'Study',
  research: 'Research',
  viva: 'Viva',
  evaluation: 'Evaluation',
}

function StatCard({ label, value, sub }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-slate-900">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [activity, setActivity] = useState(null)
  const [health, setHealth] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getStats(), getActivity(10), client.get('/health').then((r) => r.data.data)])
      .then(([s, a, h]) => {
        setStats(s)
        setActivity(a)
        setHealth(h)
      })
      .catch((e) => setError(errorMessage(e)))
  }, [])

  return (
    <div className="space-y-8">
      <ErrorMessage message={error} />
      {!stats && !error && <LoadingState message="Loading dashboard..." />}

      {stats && (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Documents" value={stats.documents} sub={`${stats.documents_ready} ready to use`} />
          <StatCard label="Study sessions" value={stats.study_sessions} />
          <StatCard label="Viva sessions" value={stats.viva_sessions} sub={`${stats.viva_completed} completed`} />
          <StatCard label="Prompt comparisons" value={stats.prompt_comparisons} />
        </section>
      )}

      {health && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">System status</h2>
          <ul className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-3">
            <li>Backend: <b className="text-green-700">{health.status}</b></li>
            <li>AI model: <b>{health.ai.model}</b></li>
            <li>
              API key:{' '}
              <b className={health.ai.api_key_configured ? 'text-green-700' : 'text-amber-600'}>
                {health.ai.api_key_configured ? 'configured' : 'not set yet'}
              </b>
            </li>
          </ul>
        </section>
      )}

      {activity && (
        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <h2 className="px-5 py-4 text-sm font-semibold text-slate-500 uppercase tracking-wide border-b border-slate-200">
            Recent activity
          </h2>
          {activity.length === 0 ? (
            <p className="px-5 py-8 text-center text-sm text-slate-500">
              No activity yet. Upload a document or try a study mode to get started.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {activity.map((a) => (
                <li key={a.id} className="flex items-center gap-3 px-5 py-3 text-sm">
                  <span className="w-20 shrink-0 rounded-full bg-indigo-50 px-2 py-0.5 text-center text-xs font-medium text-indigo-700">
                    {ACTIVITY_LABELS[a.type] || a.type}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-slate-800">{a.description}</span>
                  <span className="shrink-0 text-xs text-slate-400">{formatTime(a.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-500 uppercase tracking-wide">Quick access</h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {NAV_ITEMS.filter((i) => i.to !== '/').map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow"
            >
              <Icon className="text-indigo-600" size={22} />
              <h3 className="mt-3 font-semibold text-slate-800">{label}</h3>
              <p className="mt-1 text-sm text-slate-500">{DESCRIPTIONS[to]}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
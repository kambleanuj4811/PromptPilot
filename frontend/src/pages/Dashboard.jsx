import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client, { errorMessage } from '../api/client'
import LoadingState from '../components/LoadingState'
import ErrorMessage from '../components/ErrorMessage'
import { NAV_ITEMS } from '../components/Sidebar'

const DESCRIPTIONS = {
  '/documents': 'Upload and manage PDFs',
  '/study': 'Explain, summarize, MCQs, revision notes',
  '/research': 'Structured paper analysis',
  '/viva': 'Practice oral exam questions',
  '/qa': 'Ask questions grounded in your documents',
  '/evaluation': 'Compare Prompt A vs Prompt B',
  '/lab': 'See prompting techniques run live',
}

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    client
      .get('/health')
      .then((r) => setHealth(r.data.data))
      .catch((e) => setError(errorMessage(e)))
  }, [])

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">System status</h2>
        {!health && !error && <LoadingState message="Checking backend..." />}
        <div className="mt-3"><ErrorMessage message={error} /></div>
        {health && (
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
        )}
      </section>

      <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        Usage statistics and recent activity will appear here once the dashboard API is built.
        Nothing is shown until real data exists.
      </section>

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
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend,
} from 'chart.js'
import { Card } from './ui'
import { formatTime } from '../utils/time'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const CRITERIA = ['accuracy', 'completeness', 'relevance', 'consistency', 'formatting']
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1)

function ScoreDetails({ scores, error }) {
  if (!scores) {
    return <p className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">Not scored: {error || 'no score available.'}</p>
  }
  return (
    <div className="mt-2 space-y-1">
      {CRITERIA.map((c) => (
        <details key={c} className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm">
          <summary className="cursor-pointer select-none">
            <span className="font-medium text-slate-700">{cap(c)}</span>
            <span className="float-right font-semibold text-slate-900">{scores[c].score}/10</span>
          </summary>
          <p className="mt-1 text-xs text-slate-600">{scores[c].justification}</p>
          {scores[c].issues.length > 0 && (
            <ul className="mt-1 list-disc pl-5 text-xs text-red-700">
              {scores[c].issues.map((x, i) => <li key={i}>{x}</li>)}
            </ul>
          )}
        </details>
      ))}
    </div>
  )
}

function Side({ title, side }) {
  return (
    <div className="min-w-0 rounded-xl border border-slate-200 p-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-slate-800">{title}</h4>
        <span className="text-sm text-slate-600">
          Overall: <b>{side.overall ?? 'n/a'}</b>
        </span>
      </div>
      <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 text-xs text-slate-800">
        {side.output || '(empty response)'}
      </pre>
      {side.checks.some((c) => c.name !== 'non_empty') && (
        <ul className="mt-2 space-y-0.5 text-xs">
          {side.checks.filter((c) => c.name !== 'non_empty').map((c) => (
            <li key={c.name} className={c.passed ? 'text-green-700' : 'text-red-700'}>
              {c.passed ? 'Pass' : 'Fail'}: {c.detail}
            </li>
          ))}
        </ul>
      )}
      <ScoreDetails scores={side.scores} error={side.error} />
    </div>
  )
}

export default function EvaluationResult({ data }) {
  const { summary } = data
  const a = summary.variants.A
  const b = summary.variants.B

  const chartData = {
    labels: [...CRITERIA.map(cap), 'Overall'],
    datasets: [
      { label: 'Prompt A', backgroundColor: '#6366f1',
        data: [...CRITERIA.map((c) => (a.criteria ? a.criteria[c] : null)), a.overall] },
      { label: 'Prompt B', backgroundColor: '#f59e0b',
        data: [...CRITERIA.map((c) => (b.criteria ? b.criteria[c] : null)), b.overall] },
    ],
  }
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: { y: { min: 0, max: 10, title: { display: true, text: 'Score (0-10)' } } },
    plugins: { legend: { position: 'bottom' } },
  }

  const headline =
    summary.winner === 'A' ? `Prompt A scored higher (+${Math.abs(summary.margin)})`
    : summary.winner === 'B' ? `Prompt B scored higher (+${Math.abs(summary.margin)})`
    : summary.winner === 'tie' ? 'Too close to call'
    : 'No winner: not enough scored responses'

  return (
    <div className="space-y-6">
      <Card>
        <p className="text-xs text-slate-400">{formatTime(data.created_at)}</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">{headline}</h2>
        <p className="mt-1 text-sm text-slate-600">
          Average overall: A {a.overall ?? 'n/a'} ({a.scored}/{a.total} scored), B {b.overall ?? 'n/a'} ({b.scored}/{b.total} scored).{' '}
          {summary.winner_margin_rule}
        </p>
        {summary.notes.map((n, i) => (
          <p key={i} className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">{n}</p>
        ))}
        <div className="mt-4 h-72"><Bar data={chartData} options={options} /></div>
        <p className="mt-4 text-xs text-slate-500">{data.disclaimer}</p>
      </Card>

      {data.results.map((r) => (
        <Card key={r.question_index}>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Test question {r.question_index + 1}</p>
          <h3 className="mt-1 font-semibold text-slate-900">{r.question}</h3>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Side title="Prompt A" side={r.a} />
            <Side title="Prompt B" side={r.b} />
          </div>
        </Card>
      ))}
    </div>
  )
}
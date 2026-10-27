import { useCallback, useEffect, useState } from 'react'
import { Scale, Plus, X } from 'lucide-react'
import { compare, getHistory, getEvaluation } from '../api/evaluation'
import { errorMessage } from '../api/client'
import ErrorMessage from '../components/ErrorMessage'
import LoadingState from '../components/LoadingState'
import EvaluationResult from '../components/EvaluationResult'
import { Card, Field, buttonCls, inputCls } from '../components/ui'
import { formatTime } from '../utils/time'

const WINNER_STYLE = {
  A: 'bg-indigo-100 text-indigo-700',
  B: 'bg-amber-100 text-amber-700',
  tie: 'bg-slate-200 text-slate-700',
  unavailable: 'bg-slate-100 text-slate-500',
}

export default function PromptEvaluation() {
  const [promptA, setPromptA] = useState('')
  const [promptB, setPromptB] = useState('')
  const [questions, setQuestions] = useState([''])
  const [format, setFormat] = useState('text')
  const [fields, setFields] = useState('')
  const [maxWords, setMaxWords] = useState('')
  const [loading, setLoading] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState(null)

  const refreshHistory = useCallback(() => {
    getHistory().then(setHistory).catch((e) => setError(errorMessage(e)))
  }, [])
  useEffect(refreshHistory, [refreshHistory])

  const setQuestion = (i, v) => setQuestions(questions.map((q, idx) => (idx === i ? v : q)))

  async function submit(e) {
    e.preventDefault()
    setError('')
    const cleaned = questions.map((q) => q.trim()).filter(Boolean)
    if (promptA.trim().length < 3 || promptB.trim().length < 3) return setError('Enter both prompts (at least 3 characters each).')
    if (cleaned.length === 0) return setError('Enter at least one test question.')
    setLoading('Running both prompts and scoring the results. This can take a minute or more...')
    setResult(null)
    try {
      const data = await compare({
        prompt_a: promptA.trim(),
        prompt_b: promptB.trim(),
        test_questions: cleaned,
        expected_format: format,
        required_fields: format === 'json' ? fields.split(',').map((f) => f.trim()).filter(Boolean) : [],
        max_words: maxWords ? Number(maxWords) : null,
      })
      setResult(data)
      refreshHistory()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading('')
    }
  }

  async function openHistory(id) {
    setError('')
    setLoading('Loading saved evaluation...')
    try {
      setResult(await getEvaluation(id))
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <p className="text-sm text-slate-600">
            Each prompt is used as the system instruction for every test question. An AI judge then scores both
            responses on the same five criteria. Each question costs 4 AI calls (2 runs and 2 judgements).
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            <Field label="Prompt A" htmlFor="pa">
              <textarea id="pa" rows={5} className={inputCls} value={promptA} maxLength={4000}
                onChange={(e) => setPromptA(e.target.value)} />
            </Field>
            <Field label="Prompt B" htmlFor="pb">
              <textarea id="pb" rows={5} className={inputCls} value={promptB} maxLength={4000}
                onChange={(e) => setPromptB(e.target.value)} />
            </Field>
          </div>

          <div>
            <p className="mb-1 text-sm font-medium text-slate-700">Test questions (up to 3)</p>
            <div className="space-y-2">
              {questions.map((q, i) => (
                <div key={i} className="flex gap-2">
                  <input className={inputCls} value={q} maxLength={1000} aria-label={`Test question ${i + 1}`}
                    onChange={(e) => setQuestion(i, e.target.value)} />
                  {questions.length > 1 && (
                    <button type="button" aria-label={`Remove question ${i + 1}`}
                      onClick={() => setQuestions(questions.filter((_, idx) => idx !== i))}
                      className="text-slate-400 hover:text-red-600"><X size={18} /></button>
                  )}
                </div>
              ))}
            </div>
            {questions.length < 3 && (
              <button type="button" onClick={() => setQuestions([...questions, ''])}
                className="mt-2 inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline">
                <Plus size={14} /> Add question
              </button>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Expected format" htmlFor="fmt" hint="JSON enables exact automatic checks.">
              <select id="fmt" className={inputCls} value={format} onChange={(e) => setFormat(e.target.value)}>
                <option value="text">Plain text</option>
                <option value="json">Raw JSON</option>
              </select>
            </Field>
            {format === 'json' && (
              <Field label="Required JSON fields" htmlFor="rf" hint="Comma-separated, optional.">
                <input id="rf" className={inputCls} value={fields} onChange={(e) => setFields(e.target.value)} />
              </Field>
            )}
            <Field label="Max words (optional)" htmlFor="mw">
              <input id="mw" type="number" min={1} max={5000} className={inputCls} value={maxWords}
                onChange={(e) => setMaxWords(e.target.value)} />
            </Field>
          </div>

          <button type="submit" disabled={!!loading} className={buttonCls}>
            <Scale size={16} /> Compare prompts
          </button>
        </form>
      </Card>

      <ErrorMessage message={error} />
      {loading && <LoadingState message={loading} />}
      {result && <EvaluationResult data={result} />}

      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <h2 className="px-5 py-4 text-sm font-semibold text-slate-500 uppercase tracking-wide border-b border-slate-200">
          Evaluation history
        </h2>
        {!history && <div className="px-5"><LoadingState /></div>}
        {history?.length === 0 && (
          <p className="px-5 py-8 text-center text-sm text-slate-500">No comparisons yet. Run one above.</p>
        )}
        <ul className="divide-y divide-slate-100">
          {history?.map((h) => (
            <li key={h.id}>
              <button onClick={() => openHistory(h.id)}
                className="flex w-full items-center gap-3 px-5 py-3 text-left text-sm hover:bg-slate-50">
                <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${WINNER_STYLE[h.winner]}`}>
                  {h.winner === 'tie' ? 'Tie' : h.winner === 'unavailable' ? 'No result' : `${h.winner} wins`}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-slate-800">A: {h.prompt_a}</span>
                  <span className="block truncate text-slate-500">B: {h.prompt_b}</span>
                </span>
                <span className="shrink-0 text-xs text-slate-500">
                  {h.overall_a ?? '-'} vs {h.overall_b ?? '-'}
                </span>
                <span className="hidden shrink-0 text-xs text-slate-400 sm:block">{formatTime(h.created_at)}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
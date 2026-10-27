import { useEffect, useState } from 'react'
import { Play } from 'lucide-react'
import { getTechniques, runTechnique } from '../api/promptLab'
import { errorMessage } from '../api/client'
import ErrorMessage from '../components/ErrorMessage'
import LoadingState from '../components/LoadingState'
import { Card, Field, buttonCls, inputCls } from '../components/ui'

const Pre = ({ children }) => (
  <pre className="mt-1 max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 text-xs text-slate-800">
    {children}
  </pre>
)

export default function PromptLab() {
  const [techniques, setTechniques] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState({}) // technique id -> last run

  useEffect(() => {
    getTechniques()
      .then((t) => {
        setTechniques(t)
        setSelectedId(t[0].id)
        setInput(t[0].default_input)
      })
      .catch((e) => setError(errorMessage(e)))
  }, [])

  const selected = techniques?.find((t) => t.id === selectedId)

  function select(t) {
    setSelectedId(t.id)
    setInput(t.default_input)
    setError('')
  }

  async function run() {
    setError('')
    setLoading(true)
    try {
      const data = await runTechnique(selected.id, input)
      setResults((r) => ({ ...r, [selected.id]: data }))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  if (!techniques) {
    return error ? <ErrorMessage message={error} /> : <LoadingState message="Loading techniques..." />
  }

  const result = results[selectedId]

  return (
    <div className="grid gap-6 lg:grid-cols-[16rem_1fr]">
      <nav className="space-y-1" aria-label="Techniques">
        {techniques.map((t) => (
          <button key={t.id} onClick={() => select(t)}
            className={`block w-full rounded-lg px-3 py-2 text-left text-sm font-medium ${
              t.id === selectedId ? 'bg-indigo-600 text-white' : 'bg-white text-slate-700 hover:bg-indigo-50 border border-slate-200'
            }`}>
            {t.name}
          </button>
        ))}
      </nav>

      <div className="min-w-0 space-y-4">
        <Card>
          <h2 className="text-lg font-semibold text-slate-900">{selected.name}</h2>
          <p className="mt-2 text-sm text-slate-700">{selected.explanation}</p>
          <h3 className="mt-4 text-sm font-semibold text-slate-500 uppercase tracking-wide">Example prompt</h3>
          <Pre>{selected.example_prompt}</Pre>
          <h3 className="mt-4 text-sm font-semibold text-slate-500 uppercase tracking-wide">Why it is used</h3>
          <p className="mt-1 text-sm text-slate-700">{selected.why}</p>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Run it live</h3>
          <div className="mt-3 space-y-3">
            <Field label={selected.input_label} htmlFor="lab-input" hint={selected.input_hint}>
              <input id="lab-input" className={inputCls} value={input} maxLength={500}
                onChange={(e) => setInput(e.target.value)} />
            </Field>
            <button onClick={run} disabled={loading} className={buttonCls}>
              <Play size={16} /> {loading ? 'Running...' : 'Run demonstration'}
            </button>
            <p className="text-xs text-slate-500">
              Uses {selected.model_calls} real AI call{selected.model_calls > 1 ? 's' : ''}. Responses vary between runs.
            </p>
          </div>
          <div className="mt-3"><ErrorMessage message={error} /></div>
          {loading && <LoadingState message="Calling the AI model..." />}
        </Card>

        {result && !loading && (
          <Card>
            <p className="text-xs text-slate-500">Model: {result.model} | Input: {result.input}</p>
            {result.steps.map((s, i) => (
              <div key={i} className="mt-4">
                <h3 className="text-sm font-semibold text-slate-800">{s.label}</h3>
                <p className="mt-2 text-xs font-medium uppercase tracking-wide text-slate-500">Prompt sent</p>
                <Pre>{s.prompt}</Pre>
                <p className="mt-2 text-xs font-medium uppercase tracking-wide text-slate-500">Model output</p>
                <Pre>{s.output}</Pre>
              </div>
            ))}
            {result.validation && (
              <div className={`mt-4 rounded-lg p-3 text-sm ${result.validation.valid ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                Validation against {result.validation.schema}:{' '}
                <b>{result.validation.valid ? 'valid' : 'invalid'}</b> after {result.validation.attempts} of at most{' '}
                {result.validation.max_attempts} attempt(s).
                {result.validation.errors.map((er, i) => <p key={i} className="mt-1 text-xs">Problem: {er}</p>)}
              </div>
            )}
            {result.steps.length > 1 && (
              <>
                <h3 className="mt-4 text-sm font-semibold text-slate-800">Final output</h3>
                <Pre>{result.final_output}</Pre>
              </>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}
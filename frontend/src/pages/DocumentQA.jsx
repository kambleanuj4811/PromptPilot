import { useState } from 'react'
import { Send, FileText } from 'lucide-react'
import { askQuestion } from '../api/chat'
import { errorMessage } from '../api/client'
import DocumentSelect from '../components/DocumentSelect'
import ErrorMessage from '../components/ErrorMessage'
import LoadingState from '../components/LoadingState'
import SourceList from '../components/SourceList'
import { Card, Field, buttonCls, inputCls } from '../components/ui'

const STATUS = {
  answered: { label: 'Answer supported by document quotes', cls: 'bg-green-100 text-green-700' },
  unverified: { label: 'Unverified: quotes not found in document', cls: 'bg-amber-100 text-amber-700' },
  insufficient_evidence: { label: 'Not enough evidence in the document', cls: 'bg-slate-200 text-slate-700' },
}

export default function DocumentQA() {
  const [question, setQuestion] = useState('')
  const [documentId, setDocumentId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setError('')
    if (question.trim().length < 3) return setError('Type a question (at least 3 characters).')
    setLoading(true)
    setResult(null)
    try {
      setResult(await askQuestion(question.trim(), documentId ? [documentId] : null))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const badge = result && STATUS[result.status]

  return (
    <div className="space-y-6">
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <Field label="Search in" htmlFor="doc">
            <DocumentSelect id="doc" value={documentId} onChange={setDocumentId} emptyLabel="All my documents" />
          </Field>
          <Field label="Your question" htmlFor="q">
            <textarea id="q" rows={3} className={inputCls} value={question} maxLength={1000}
              onChange={(e) => setQuestion(e.target.value)} />
          </Field>
          <button type="submit" disabled={loading} className={buttonCls}>
            <Send size={16} /> {loading ? 'Searching...' : 'Ask'}
          </button>
        </form>
      </Card>

      <ErrorMessage message={error} />
      {loading && <LoadingState message="Retrieving passages and generating an answer..." />}

      {result && (
        <Card>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${badge.cls}`}>{badge.label}</span>
          {result.warning && <p className="mt-3 rounded-lg bg-amber-50 p-2 text-sm text-amber-800">{result.warning}</p>}

          <h3 className="mt-4 text-sm font-semibold text-slate-500 uppercase tracking-wide">Answer</h3>
          <p className="mt-1 text-sm leading-relaxed text-slate-800">{result.answer}</p>

          {result.evidence.length > 0 && (
            <>
              <h3 className="mt-5 text-sm font-semibold text-slate-500 uppercase tracking-wide">
                Evidence from your documents
              </h3>
              <ul className="mt-2 space-y-2">
                {result.evidence.map((ev, i) => (
                  <li key={i} className="rounded-lg border-l-4 border-green-500 bg-green-50 p-3 text-sm">
                    <p className="italic text-slate-800">"{ev.quote}"</p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-slate-600">
                      <FileText size={12} /> {ev.filename}, page {ev.page_number}
                    </p>
                  </li>
                ))}
              </ul>
            </>
          )}

          {result.explanation && (
            <>
              <h3 className="mt-5 text-sm font-semibold text-slate-500 uppercase tracking-wide">
                AI explanation (interpretation, not a quote)
              </h3>
              <p className="mt-1 text-sm text-slate-700">{result.explanation}</p>
            </>
          )}

          <SourceList sources={result.sources} />
          <p className="mt-6 text-xs text-slate-400">{result.disclaimer}</p>
        </Card>
      )}
    </div>
  )
}
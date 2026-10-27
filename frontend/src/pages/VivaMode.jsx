import { useState } from 'react'
import { Mic } from 'lucide-react'
import { startViva, evaluateAnswer, nextQuestion } from '../api/viva'
import { errorMessage } from '../api/client'
import DocumentSelect from '../components/DocumentSelect'
import ErrorMessage from '../components/ErrorMessage'
import LoadingState from '../components/LoadingState'
import { Card, Field, buttonCls, inputCls } from '../components/ui'

const Warning = ({ text }) => (
  <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">{text}</p>
)

function Score({ label, value }) {
  const cls = value >= 7 ? 'bg-green-100 text-green-700' : value >= 4 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
  return (
    <div className={`rounded-xl px-4 py-3 text-center ${cls}`}>
      <p className="text-2xl font-semibold">{value}<span className="text-sm">/10</span></p>
      <p className="text-xs">{label}</p>
    </div>
  )
}

const Bullets = ({ title, items }) =>
  items?.length > 0 && (
    <div>
      <h4 className="text-sm font-semibold text-slate-600">{title}</h4>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-800">
        {items.map((x, i) => <li key={i}>{x}</li>)}
      </ul>
    </div>
  )

export default function VivaMode() {
  const [phase, setPhase] = useState('setup') // setup | question | feedback | summary
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('medium')
  const [count, setCount] = useState(5)
  const [documentId, setDocumentId] = useState('')

  const [session, setSession] = useState(null) // {session_id, total, disclaimer, notes}
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState('')
  const [error, setError] = useState('')

  async function guarded(label, fn) {
    setError('')
    setLoading(label)
    try {
      await fn()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading('')
    }
  }

  const start = (e) => {
    e.preventDefault()
    if (!topic.trim()) return setError('Enter a subject or topic.')
    guarded('Generating viva questions...', async () => {
      const data = await startViva({
        topic, difficulty, count: Number(count), document_id: documentId || null,
      })
      setSession(data)
      setQuestion(data.question)
      setAnswer('')
      setFeedback(null)
      setSummary(null)
      setPhase('question')
    })
  }

  const submitAnswer = (e) => {
    e.preventDefault()
    if (!answer.trim()) return setError('Write an answer before submitting.')
    guarded('Evaluating your answer...', async () => {
      setFeedback(await evaluateAnswer(session.session_id, answer))
      setPhase('feedback')
    })
  }

  const goNext = () =>
    guarded(feedback.is_last ? 'Preparing your summary...' : 'Loading next question...', async () => {
      const data = await nextQuestion(session.session_id)
      if (data.completed) {
        setSummary(data.summary)
        setPhase('summary')
      } else {
        setQuestion(data.question)
        setAnswer('')
        setFeedback(null)
        setPhase('question')
      }
    })

  function reset() {
    setPhase('setup')
    setSession(null)
    setQuestion(null)
    setFeedback(null)
    setSummary(null)
    setAnswer('')
    setError('')
  }

  return (
    <div className="space-y-6">
      <Warning text="AI-generated grading is an estimate, not an authoritative academic assessment." />
      <ErrorMessage message={error} />
      {loading && <LoadingState message={loading} />}

      {phase === 'setup' && (
        <Card>
          <form onSubmit={start} className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Field label="Subject or topic" htmlFor="topic">
                <input id="topic" className={inputCls} value={topic} maxLength={300}
                  onChange={(e) => setTopic(e.target.value)} />
              </Field>
            </div>
            <Field label="Difficulty" htmlFor="diff">
              <select id="diff" className={inputCls} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </Field>
            <Field label="Number of questions" htmlFor="count">
              <input id="count" type="number" min={1} max={10} className={inputCls} value={count}
                onChange={(e) => setCount(e.target.value)} />
            </Field>
            <div className="sm:col-span-2">
              <Field label="Base questions on a document (optional)" htmlFor="doc">
                <DocumentSelect id="doc" value={documentId} onChange={setDocumentId} emptyLabel="No document" />
              </Field>
            </div>
            <div className="sm:col-span-2">
              <button type="submit" disabled={!!loading} className={buttonCls}>
                <Mic size={16} /> Start viva
              </button>
            </div>
          </form>
        </Card>
      )}

      {(phase === 'question' || phase === 'feedback') && question && (
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Question {question.number} of {question.total} - {session.topic}
          </p>
          <h2 className="mt-2 text-lg font-semibold text-slate-900">{question.question}</h2>
          {session.notes?.map((n, i) => <p key={i} className="mt-2 text-xs text-amber-700">{n}</p>)}

          {phase === 'question' && (
            <form onSubmit={submitAnswer} className="mt-4 space-y-3">
              <label htmlFor="answer" className="sr-only">Your answer</label>
              <textarea id="answer" rows={6} className={inputCls} value={answer} maxLength={4000}
                placeholder="Answer as you would in an oral exam..."
                onChange={(e) => setAnswer(e.target.value)} />
              <button type="submit" disabled={!!loading} className={buttonCls}>Submit answer</button>
            </form>
          )}

          {phase === 'feedback' && feedback && (
            <div className="mt-4 space-y-4">
              <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                <b>Your answer: </b>{answer}
              </div>
              <div className="grid max-w-xs grid-cols-2 gap-3">
                <Score label="Correctness" value={feedback.evaluation.correctness} />
                <Score label="Understanding" value={feedback.evaluation.conceptual_understanding} />
              </div>
              <p className="text-sm text-slate-800">{feedback.evaluation.feedback}</p>
              <Bullets title="Strengths" items={feedback.evaluation.strengths} />
              <Bullets title="Weaknesses" items={feedback.evaluation.weaknesses} />
              <div className="rounded-lg border-l-4 border-indigo-500 bg-indigo-50 p-3">
                <h4 className="text-sm font-semibold text-indigo-800">Improved model answer</h4>
                <p className="mt-1 text-sm text-slate-800">{feedback.evaluation.improved_answer}</p>
              </div>
              <button onClick={goNext} disabled={!!loading} className={buttonCls}>
                {feedback.is_last ? 'Finish and see summary' : 'Next question'}
              </button>
            </div>
          )}
        </Card>
      )}

      {phase === 'summary' && summary && (
        <Card>
          <h2 className="text-lg font-semibold text-slate-900">Session summary</h2>
          <p className="mt-1 text-sm text-slate-500">
            {summary.questions_answered} of {summary.total_questions} questions answered
          </p>
          <div className="mt-4 grid max-w-xs grid-cols-2 gap-3">
            <Score label="Avg correctness" value={summary.average_correctness} />
            <Score label="Avg understanding" value={summary.average_conceptual_understanding} />
          </div>
          <p className="mt-4 text-sm text-slate-800">{summary.overall_assessment}</p>
          <div className="mt-4 space-y-4">
            <Bullets title="Strengths" items={summary.strengths} />
            <Bullets title="Areas for improvement" items={summary.areas_for_improvement} />
            <Bullets title="Study suggestions" items={summary.study_suggestions} />
          </div>
          <p className="mt-6 text-xs text-slate-400">{summary.disclaimer}</p>
          <button onClick={reset} className={`${buttonCls} mt-4`}>Start a new viva</button>
        </Card>
      )}
    </div>
  )
}
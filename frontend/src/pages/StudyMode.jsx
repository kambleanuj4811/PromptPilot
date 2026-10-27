import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { runStudy } from '../api/study'
import { errorMessage } from '../api/client'
import DocumentSelect from '../components/DocumentSelect'
import ErrorMessage from '../components/ErrorMessage'
import LoadingState from '../components/LoadingState'
import ResponseRenderer from '../components/ResponseRenderer'
import SourceList from '../components/SourceList'
import { Card, Field, buttonCls, inputCls } from '../components/ui'

const OPERATIONS = [
  { id: 'explain', label: 'Explain a topic' },
  { id: 'summarize', label: 'Summarize notes' },
  { id: 'revision_notes', label: 'Revision notes' },
  { id: 'mcqs', label: 'Generate MCQs' },
  { id: 'questions', label: 'Short-answer questions' },
  { id: 'exam_answer', label: 'Exam-ready answer' },
]

export default function StudyMode() {
  const [operation, setOperation] = useState('explain')
  const [topic, setTopic] = useState('')
  const [text, setText] = useState('')
  const [level, setLevel] = useState('undergraduate')
  const [length, setLength] = useState('medium')
  const [style, setStyle] = useState('simple')
  const [count, setCount] = useState(5)
  const [documentId, setDocumentId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [output, setOutput] = useState(null)

  const isSummarize = operation === 'summarize'
  const isCounted = operation === 'mcqs' || operation === 'questions'
  const usesLength = !isCounted

  async function submit(e) {
    e.preventDefault()
    setError('')
    if (isSummarize && !text.trim() && !documentId) {
      return setError('Paste some notes or select a document to summarize.')
    }
    if (!isSummarize && !topic.trim()) {
      return setError(operation === 'exam_answer' ? 'Enter the exam question.' : 'Enter a topic.')
    }
    setLoading(true)
    setOutput(null)
    try {
      const data = await runStudy(operation, {
        topic, text, academic_level: level, length, style,
        count: Number(count), document_id: documentId || null,
      })
      setOutput(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <Field label="What do you want to do?" htmlFor="op">
            <select id="op" className={inputCls} value={operation}
              onChange={(e) => { setOperation(e.target.value); setOutput(null); setError('') }}>
              {OPERATIONS.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
            </select>
          </Field>

          <Field
            label={operation === 'exam_answer' ? 'Exam question' : isSummarize ? 'Focus (optional)' : 'Topic'}
            htmlFor="topic"
          >
            <input id="topic" className={inputCls} value={topic} maxLength={300}
              onChange={(e) => setTopic(e.target.value)} />
          </Field>

          {isSummarize && (
            <Field label="Paste notes" htmlFor="text" hint="Or select a document below.">
              <textarea id="text" rows={5} className={inputCls} value={text} maxLength={20000}
                onChange={(e) => setText(e.target.value)} />
            </Field>
          )}

          <Field label="Document context (optional)" htmlFor="doc"
            hint="Output is based on the selected document's content.">
            <DocumentSelect id="doc" value={documentId} onChange={setDocumentId} emptyLabel="No document" />
          </Field>

          <Field label="Academic level" htmlFor="level">
            <select id="level" className={inputCls} value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="school">School</option>
              <option value="undergraduate">Undergraduate</option>
              <option value="postgraduate">Postgraduate</option>
              <option value="professional">Professional</option>
            </select>
          </Field>

          {usesLength && (
            <Field label="Answer length" htmlFor="length">
              <select id="length" className={inputCls} value={length} onChange={(e) => setLength(e.target.value)}>
                <option value="short">Short</option>
                <option value="medium">Medium</option>
                <option value="detailed">Detailed</option>
              </select>
            </Field>
          )}

          {isCounted && (
            <Field label="Number of questions" htmlFor="count">
              <input id="count" type="number" min={1} max={10} className={inputCls} value={count}
                onChange={(e) => setCount(e.target.value)} />
            </Field>
          )}

          <Field label="Output style" htmlFor="style">
            <select id="style" className={inputCls} value={style} onChange={(e) => setStyle(e.target.value)}>
              <option value="simple">Simple</option>
              <option value="exam">Exam-oriented</option>
              <option value="technical">Technical</option>
            </select>
          </Field>

          <button type="submit" disabled={loading} className={buttonCls}>
            <Sparkles size={16} /> {loading ? 'Generating...' : 'Generate'}
          </button>
        </form>
      </Card>

      <div className="space-y-4">
        <ErrorMessage message={error} />
        {loading && <LoadingState message="Generating with AI..." />}
        {!loading && !output && !error && (
          <Card><p className="text-sm text-slate-500">Choose an operation, fill the form and press Generate. Results appear here.</p></Card>
        )}
        {output && (
          <Card>
            <ResponseRenderer operation={output.operation} result={output.result} />
            {output.notes.map((n, i) => (
              <p key={i} className="mt-4 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">{n}</p>
            ))}
            <SourceList sources={output.sources} />
            <p className="mt-6 text-xs text-slate-400">AI-generated content can contain mistakes. Verify important facts.</p>
          </Card>
        )}
      </div>
    </div>
  )
}
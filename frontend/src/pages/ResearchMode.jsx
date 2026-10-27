import { useState } from 'react'
import { Microscope, FileText } from 'lucide-react'
import { analyzePaper, summarizePaper } from '../api/research'
import { errorMessage } from '../api/client'
import DocumentSelect from '../components/DocumentSelect'
import ErrorMessage from '../components/ErrorMessage'
import LoadingState from '../components/LoadingState'
import SourceList from '../components/SourceList'
import { Card, Field, buttonCls } from '../components/ui'

const ASPECTS = [
  ['objectives', 'Research objectives'],
  ['methodology', 'Methodology'],
  ['key_findings', 'Key findings'],
  ['limitations', 'Limitations'],
  ['conclusions', 'Conclusions'],
]

const secondaryBtn =
  'inline-flex items-center gap-2 rounded-lg border border-indigo-600 px-4 py-2 text-sm font-medium ' +
  'text-indigo-700 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-50'

function Aspect({ title, aspect }) {
  return (
    <section className="mt-5">
      <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{title}</h3>
      {!aspect.found_in_document ? (
        <p className="mt-1 text-sm text-slate-500">
          Not clearly stated in the retrieved excerpts, so nothing is reported here.
        </p>
      ) : (
        <ul className="mt-2 space-y-3">
          {aspect.findings.map((f, i) => (
            <li key={i} className="text-sm text-slate-800">
              <p>{f.statement}</p>
              <p className="mt-1 rounded-lg border-l-4 border-green-500 bg-green-50 p-2 italic">"{f.quote}"</p>
              <p className="mt-1 flex items-center gap-1 text-xs text-slate-600">
                <FileText size={12} /> {f.filename}, page {f.page_number}
              </p>
            </li>
          ))}
        </ul>
      )}
      {aspect.interpretation && (
        <p className="mt-2 text-sm text-slate-600">
          <b>AI interpretation (not a claim from the paper): </b>
          {aspect.interpretation}
        </p>
      )}
    </section>
  )
}

export default function ResearchMode() {
  const [documentId, setDocumentId] = useState('')
  const [loading, setLoading] = useState('')
  const [error, setError] = useState('')
  const [output, setOutput] = useState(null)

  async function run(kind) {
    setError('')
    if (!documentId) return setError('Select a paper first.')
    setLoading(kind)
    setOutput(null)
    try {
      const data = kind === 'analysis' ? await analyzePaper(documentId) : await summarizePaper(documentId)
      setOutput({ kind, data })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <div className="space-y-4">
          <Field label="Research paper" htmlFor="paper" hint="Upload papers on the Documents page first.">
            <DocumentSelect id="paper" value={documentId} onChange={setDocumentId} emptyLabel="Select a paper..." />
          </Field>
          <div className="flex flex-wrap gap-3">
            <button className={buttonCls} disabled={!!loading} onClick={() => run('analysis')}>
              <Microscope size={16} /> {loading === 'analysis' ? 'Analysing...' : 'Structured analysis'}
            </button>
            <button className={secondaryBtn} disabled={!!loading} onClick={() => run('summary')}>
              {loading === 'summary' ? 'Summarising...' : 'Summary only'}
            </button>
          </div>
        </div>
      </Card>

      <ErrorMessage message={error} />
      {loading && <LoadingState message="Reading the paper and generating the analysis..." />}

      {output && (
        <Card>
          <h2 className="text-lg font-semibold text-slate-900">{output.data.document.filename}</h2>

          {output.kind === 'analysis' ? (
            <>
              <section className="mt-4">
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
                  Overview (AI-written summary)
                </h3>
                <p className="mt-1 text-sm text-slate-800">{output.data.analysis.overview}</p>
              </section>
              {ASPECTS.map(([key, title]) => (
                <Aspect key={key} title={title} aspect={output.data.analysis[key]} />
              ))}
            </>
          ) : (
            <>
              <p className="mt-4 text-sm leading-relaxed text-slate-800">{output.data.summary.summary}</p>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-800">
                {output.data.summary.key_points.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </>
          )}

          {output.data.notes.map((n, i) => (
            <p key={i} className="mt-4 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">{n}</p>
          ))}
          <SourceList sources={output.data.sources} />
          <p className="mt-6 text-xs text-slate-400">{output.data.disclaimer}</p>
        </Card>
      )}
    </div>
  )
}
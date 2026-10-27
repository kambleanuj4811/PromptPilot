import { useState } from 'react'

const Block = ({ title, children }) => (
  <section className="mt-4">
    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{title}</h3>
    <div className="mt-1 text-sm leading-relaxed text-slate-800">{children}</div>
  </section>
)

const List = ({ items }) => (
  <ul className="list-disc space-y-1 pl-5">
    {items.map((x, i) => <li key={i}>{x}</li>)}
  </ul>
)

function Mcq({ q, number }) {
  const [picked, setPicked] = useState(null)
  return (
    <div className="mt-4 rounded-xl border border-slate-200 p-4">
      <p className="font-medium text-slate-800">{number}. {q.question}</p>
      <div className="mt-2 space-y-2">
        {q.options.map((opt, i) => {
          let style = 'border-slate-300 hover:border-indigo-300'
          if (picked !== null && i === q.correct_index) style = 'border-green-500 bg-green-50'
          else if (picked === i) style = 'border-red-400 bg-red-50'
          return (
            <button
              key={i}
              disabled={picked !== null}
              onClick={() => setPicked(i)}
              className={`block w-full rounded-lg border px-3 py-2 text-left text-sm ${style}`}
            >
              {String.fromCharCode(65 + i)}. {opt}
            </button>
          )
        })}
      </div>
      {picked !== null && (
        <p className="mt-3 text-sm text-slate-700">
          <b>{picked === q.correct_index ? 'Correct. ' : `Incorrect. The answer is ${String.fromCharCode(65 + q.correct_index)}. `}</b>
          {q.explanation}
        </p>
      )}
    </div>
  )
}

function ShortQuestion({ q, number }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-4 rounded-xl border border-slate-200 p-4">
      <p className="font-medium text-slate-800">
        {number}. {q.question} <span className="text-xs text-slate-500">({q.marks} marks)</span>
      </p>
      <button onClick={() => setOpen(!open)} className="mt-2 text-sm text-indigo-600 hover:underline">
        {open ? 'Hide model answer' : 'Show model answer'}
      </button>
      {open && <p className="mt-2 text-sm text-slate-700">{q.model_answer}</p>}
    </div>
  )
}

export default function ResponseRenderer({ operation, result }) {
  switch (operation) {
    case 'explain':
      return (
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{result.title}</h2>
          <Block title="Overview"><p>{result.overview}</p></Block>
          <Block title="Key points"><List items={result.key_points} /></Block>
          <Block title="Example"><p>{result.example}</p></Block>
          {result.common_mistakes.length > 0 && (
            <Block title="Common mistakes"><List items={result.common_mistakes} /></Block>
          )}
          <Block title="Summary"><p>{result.summary}</p></Block>
        </div>
      )
    case 'summarize':
      return (
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{result.title}</h2>
          <Block title="Summary"><p>{result.summary}</p></Block>
          <Block title="Key points"><List items={result.key_points} /></Block>
        </div>
      )
    case 'revision_notes':
      return (
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{result.title}</h2>
          {result.sections.map((s, i) => (
            <Block key={i} title={s.heading}><List items={s.points} /></Block>
          ))}
          {result.key_terms.length > 0 && (
            <Block title="Key terms">
              <dl className="space-y-1">
                {result.key_terms.map((t, i) => (
                  <div key={i}><dt className="inline font-semibold">{t.term}: </dt><dd className="inline">{t.definition}</dd></div>
                ))}
              </dl>
            </Block>
          )}
        </div>
      )
    case 'mcqs':
      return <div>{result.questions.map((q, i) => <Mcq key={i} q={q} number={i + 1} />)}</div>
    case 'questions':
      return <div>{result.questions.map((q, i) => <ShortQuestion key={i} q={q} number={i + 1} />)}</div>
    case 'exam_answer':
      return (
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{result.question}</h2>
          <Block title="Introduction"><p>{result.introduction}</p></Block>
          {result.sections.map((s, i) => (
            <Block key={i} title={s.heading}><p>{s.content}</p></Block>
          ))}
          <Block title="Conclusion"><p>{result.conclusion}</p></Block>
          {result.keywords.length > 0 && <Block title="Keywords"><p>{result.keywords.join(', ')}</p></Block>}
        </div>
      )
    default:
      return null
  }
}
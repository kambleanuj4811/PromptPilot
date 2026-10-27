import { useEffect, useState } from 'react'
import { listDocuments } from '../api/documents'
import { inputCls } from './ui'

// Shows only documents that finished processing. value "" means "no specific document".
export default function DocumentSelect({ id, value, onChange, emptyLabel }) {
  const [docs, setDocs] = useState(null)

  useEffect(() => {
    listDocuments()
      .then((all) => setDocs(all.filter((d) => d.status === 'ready')))
      .catch(() => setDocs([]))
  }, [])

  return (
    <div>
      <select id={id} className={inputCls} value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">{emptyLabel}</option>
        {docs?.map((d) => (
          <option key={d.id} value={d.id}>{d.original_filename}</option>
        ))}
      </select>
      {docs && docs.length === 0 && (
        <p className="mt-1 text-xs text-amber-600">No ready documents yet. Upload one on the Documents page.</p>
      )}
    </div>
  )
}
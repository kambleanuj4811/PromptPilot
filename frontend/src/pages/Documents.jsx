import { useCallback, useEffect, useState } from 'react'
import { Trash2, FileText } from 'lucide-react'
import { listDocuments, uploadDocument, deleteDocument } from '../api/documents'
import { errorMessage } from '../api/client'
import FileUploader from '../components/FileUploader'
import LoadingState from '../components/LoadingState'
import ErrorMessage from '../components/ErrorMessage'

const BADGE = {
  ready: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  processing: 'bg-amber-100 text-amber-700',
}

export default function Documents() {
  const [docs, setDocs] = useState(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)

  const refresh = useCallback(() => {
    listDocuments().then(setDocs).catch((e) => setError(errorMessage(e)))
  }, [])

  useEffect(refresh, [refresh])

  async function handleFile(file) {
    setError('')
    setUploading(true)
    try {
      await uploadDocument(file)
      refresh()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(doc) {
    if (!window.confirm(`Delete "${doc.original_filename}"? This also removes its search index.`)) return
    try {
      await deleteDocument(doc.id)
      refresh()
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  return (
    <div className="space-y-6">
      <FileUploader onFile={handleFile} busy={uploading} />
      {uploading && (
        <LoadingState message="Processing PDF (the first upload downloads the embedding model and can take a few minutes)..." />
      )}
      <ErrorMessage message={error} />

      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <h2 className="px-5 py-4 text-sm font-semibold text-slate-500 uppercase tracking-wide border-b border-slate-200">
          Your documents
        </h2>
        {!docs && !error && <div className="px-5"><LoadingState /></div>}
        {docs && docs.length === 0 && (
          <p className="px-5 py-8 text-center text-sm text-slate-500">
            No documents yet. Upload a PDF above to get started.
          </p>
        )}
        <ul className="divide-y divide-slate-100">
          {docs?.map((d) => (
            <li key={d.id} className="flex items-start gap-3 px-5 py-4">
              <FileText className="mt-0.5 text-slate-400" size={20} />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-slate-800">{d.original_filename}</p>
                <p className="text-xs text-slate-500">
                  {d.page_count ?? '?'} pages, {d.chunk_count} chunks, {(d.file_size_bytes / 1024).toFixed(0)} KB
                </p>
                {d.error_message && <p className="mt-1 text-sm text-red-600">{d.error_message}</p>}
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE[d.status] || ''}`}>
                {d.status}
              </span>
              <button onClick={() => handleDelete(d)} className="text-slate-400 hover:text-red-600" aria-label={`Delete ${d.original_filename}`}>
                <Trash2 size={18} />
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
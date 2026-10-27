import { useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'

export default function FileUploader({ onFile, busy, maxMb = 20 }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [localError, setLocalError] = useState('')

  function handle(file) {
    setLocalError('')
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) return setLocalError('Only PDF files are supported.')
    if (file.size > maxMb * 1024 * 1024) return setLocalError(`File is larger than ${maxMb} MB.`)
    onFile(file)
  }

  return (
    <div>
      <div
        onClick={() => !busy && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); if (!busy) handle(e.dataTransfer.files[0]) }}
        className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition
          ${dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white hover:border-indigo-300'}
          ${busy ? 'opacity-60 cursor-not-allowed' : ''}`}
      >
        <UploadCloud className="mx-auto text-indigo-600" size={32} />
        <p className="mt-2 text-sm font-medium text-slate-700">Click to choose a PDF, or drag it here</p>
        <p className="text-xs text-slate-500">Up to {maxMb} MB. Text-based PDFs only (no OCR).</p>
        <input ref={inputRef} type="file" accept=".pdf,application/pdf" className="hidden"
          onChange={(e) => { handle(e.target.files[0]); e.target.value = '' }} />
      </div>
      {localError && <p className="mt-2 text-sm text-red-600">{localError}</p>}
    </div>
  )
}
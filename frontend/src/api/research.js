import client from './client'

export const analyzePaper = (documentId) =>
  client.post('/research/analyze', { document_id: documentId }).then((r) => r.data.data)

export const summarizePaper = (documentId) =>
  client.post('/research/summarize', { document_id: documentId }).then((r) => r.data.data)
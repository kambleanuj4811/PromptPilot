import client from './client'

export const listDocuments = () => client.get('/documents').then((r) => r.data.data)

export const uploadDocument = (file) => {
  const form = new FormData()
  form.append('file', file)
  // long timeout: the first upload downloads the embedding model
  return client.post('/documents/upload', form, { timeout: 600000 }).then((r) => r.data.data)
}

export const deleteDocument = (id) => client.delete(`/documents/${id}`).then((r) => r.data.data)
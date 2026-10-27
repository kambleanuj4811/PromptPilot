import client from './client'

export const askQuestion = (question, documentIds) =>
  client
    .post('/chat/ask', { question, document_ids: documentIds })
    .then((r) => r.data.data)
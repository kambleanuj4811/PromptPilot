import client from './client'

export const startViva = (body) => client.post('/viva/start', body).then((r) => r.data.data)

export const evaluateAnswer = (sessionId, answer) =>
  client.post('/viva/evaluate', { session_id: sessionId, answer }).then((r) => r.data.data)

export const nextQuestion = (sessionId) =>
  client.post('/viva/next', { session_id: sessionId }).then((r) => r.data.data)
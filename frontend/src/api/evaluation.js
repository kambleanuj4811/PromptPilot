import client from './client'

// A comparison can make up to 12 AI calls, so allow up to 5 minutes.
export const compare = (body) =>
  client.post('/evaluation/compare', body, { timeout: 300000 }).then((r) => r.data.data)

export const getHistory = () => client.get('/evaluation/history').then((r) => r.data.data)
export const getEvaluation = (id) => client.get(`/evaluation/${id}`).then((r) => r.data.data)
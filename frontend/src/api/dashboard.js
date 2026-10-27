import client from './client'

export const getStats = () => client.get('/dashboard/stats').then((r) => r.data.data)
export const getActivity = (limit = 10) =>
  client.get('/dashboard/activity', { params: { limit } }).then((r) => r.data.data)
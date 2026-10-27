import client from './client'

export const getTechniques = () => client.get('/prompt-lab/techniques').then((r) => r.data.data)

export const runTechnique = (techniqueId, userInput) =>
  client
    .post('/prompt-lab/run', { technique_id: techniqueId, user_input: userInput }, { timeout: 180000 })
    .then((r) => r.data.data)
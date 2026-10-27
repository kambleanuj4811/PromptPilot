import client from './client'

// operation -> URL path on the backend
const PATHS = {
  explain: 'explain',
  summarize: 'summarize',
  revision_notes: 'revision-notes',
  mcqs: 'mcqs',
  questions: 'questions',
  exam_answer: 'exam-answers',
}

export const runStudy = (operation, body) =>
  client.post(`/study/${PATHS[operation]}`, body).then((r) => r.data.data)
import axios from 'axios'

const jee = axios.create({
  baseURL: 'http://localhost:8001',
  timeout: 180000, // transcript can take a while
})

export default jee

export const analyzeVideo = (data) => jee.post('/analyze', data)
export const generatePYQs = (subject, chapter, n = 5) =>
  jee.post(`/generate-pyqs?subject=${subject}&chapter=${chapter}&n=${n}`)
export const askQuestion = (question, subject) =>
  jee.post(`/ask?question=${encodeURIComponent(question)}&subject=${subject}`)
export const jeeHealth = () => jee.get('/health')

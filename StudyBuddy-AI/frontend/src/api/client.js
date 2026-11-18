import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Attach student_id from localStorage to all requests
api.interceptors.request.use((config) => {
  const studentId = localStorage.getItem('student_id')
  if (studentId && config.method !== 'get') {
    // For JSON bodies
    if (config.data && typeof config.data === 'object' && !(config.data instanceof FormData)) {
      if (!config.data.student_id) config.data.student_id = studentId
    }
  }
  return config
})

export default api

// --- Students ---
export const createStudent = (data) => api.post('/students', data)
export const getStudent = (id) => api.get(`/students/${id}`)
export const updateStudent = (id, data) => api.put(`/students/${id}`, data)
export const listStudents = () => api.get('/students')

// --- Chat ---
export const sendChat = (data) => api.post('/chat', data)
export const getConversations = (studentId) => api.get(`/chat/${studentId}/conversations`)
export const getMessages = (convId) => api.get(`/chat/conversation/${convId}/messages`)

// --- Documents ---
export const uploadDocument = (formData) =>
  api.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const listDocuments = (studentId) => api.get(`/documents/${studentId}`)
export const deleteDocument = (docId) => api.delete(`/documents/${docId}`)
export const queryDocuments = (data) => api.post('/documents/query', data)

// --- Quiz ---
export const generateQuiz = (data) => api.post('/quiz/generate', data)
export const submitQuiz = (data) => api.post('/quiz/submit', data)
export const getQuizHistory = (studentId) => api.get(`/quiz/${studentId}/history`)

// --- Resume ---
export const uploadResume = (formData) =>
  api.post('/resume/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const analyzeResume = (resumeId, targetRole) =>
  api.post(`/resume/analyze/${resumeId}`, null, { params: { target_role: targetRole } })
export const matchJD = (data) => api.post('/resume/match-jd', data)
export const listResumes = (studentId) => api.get(`/resume/${studentId}/list`)

// --- Roadmap ---
export const generateRoadmap = (data) => api.post('/roadmap', data)
export const listRoadmaps = (studentId) => api.get(`/roadmap/${studentId}/list`)
export const getRoadmap = (id) => api.get(`/roadmap/${id}`)

// --- Interview ---
export const startInterview = (data) => api.post('/interview/start', data)
export const evaluateInterview = (data) => api.post('/interview/evaluate', data)
export const getInterviewHistory = (studentId) => api.get(`/interview/${studentId}/history`)

// --- Dashboard ---
export const getDashboard = (studentId) => api.get(`/dashboard/${studentId}`)
export const getAdminStudents = () => api.get('/dashboard/admin/students')

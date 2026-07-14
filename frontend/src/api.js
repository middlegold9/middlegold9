import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getDashboard = () => api.get('/synergy/dashboard').then(r => r.data)
export const getDistrictIntel = () => api.get('/synergy/district-intelligence').then(r => r.data)
export const getSynergyEvents = () => api.get('/synergy/events').then(r => r.data)

export const getClients = () => api.get('/clients').then(r => r.data)
export const getClient360 = (id) => api.get(`/clients/${id}/360`).then(r => r.data)

export const getTransactions = () => api.get('/transactions').then(r => r.data)
export const getTransactionStats = () => api.get('/transactions/stats').then(r => r.data)

export const getAuctions = () => api.get('/land-auctions').then(r => r.data)
export const getContentPipeline = () => api.get('/contents/pipeline').then(r => r.data)
export const getContents = () => api.get('/contents').then(r => r.data)

export const getMeetings = () => api.get('/meetings').then(r => r.data)
export const getMeetingBrief = (id) => api.get(`/meetings/${id}/brief`).then(r => r.data)

export const getContracts = () => api.get('/contracts').then(r => r.data)

export const uploadDocument = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/ingestion/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export default api

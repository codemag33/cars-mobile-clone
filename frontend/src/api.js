import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export const api = axios.create({
  baseURL,
  timeout: 10000,
})

export async function fetchCars(params = {}) {
  const cleanParams = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  )
  const { data } = await api.get('/api/cars', { params: cleanParams })
  return data
}

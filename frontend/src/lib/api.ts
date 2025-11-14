import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export interface AudiogramMeasurement {
  frequency_hz: number
  threshold_db: number
}

export interface UploadResponse {
  test_id: string
  confidence: number
  needs_review: boolean
  left_ear: AudiogramMeasurement[]
  right_ear: AudiogramMeasurement[]
}

export interface HearingTest {
  id: string
  test_date: string
  source_type: string
  location: string
  confidence: number
}

export const uploadAudiogram = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<UploadResponse>('/tests/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

  return response.data
}

export const listTests = async (): Promise<HearingTest[]> => {
  const response = await apiClient.get<HearingTest[]>('/tests')
  return response.data
}

export const updateTest = async (testId: string, data: {
  test_date: string
  location?: string
  device_name?: string
  notes?: string
  left_ear: AudiogramMeasurement[]
  right_ear: AudiogramMeasurement[]
}): Promise<UploadResponse> => {
  const response = await apiClient.put<UploadResponse>(`/tests/${testId}`, data)
  return response.data
}

export const deleteTest = async (testId: string): Promise<void> => {
  await apiClient.delete(`/tests/${testId}`)
}

export interface TestDetail {
  id: string
  test_date: string
  source_type: string
  location: string
  left_ear: AudiogramMeasurement[]
  right_ear: AudiogramMeasurement[]
  metadata: {
    device: string
    technician: string
    notes: string
  }
}

export const getTest = async (testId: string): Promise<TestDetail> => {
  const response = await apiClient.get<TestDetail>(`/tests/${testId}`)
  return response.data
}

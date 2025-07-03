import axios, { AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface QueryRequest {
  query: string
  session_id?: string
}

export interface QueryResponse {
  query: string
  response: string
  session_id: string
  timestamp: string
  processing_time: number
}

export interface JobResponse {
  job_id: string
  status: 'processing' | 'completed' | 'failed'
  result?: QueryResponse
  error?: string
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const cagApi = {
  // Synchronous query (waits for response)
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    console.log('Sending query:', request)
    const { data } = await api.post<QueryResponse>('/query', request)
    console.log('Query response:', data)
    return data
  },

  // Asynchronous query (returns job ID)
  queryAsync: async (request: QueryRequest): Promise<{ job_id: string }> => {
    console.log('Sending async query:', request)
    const { data } = await api.post<{ job_id: string }>('/query/async', request)
    console.log('Async query response:', data)
    return data
  },

  // Check job status
  getJobStatus: async (jobId: string): Promise<JobResponse> => {
    const { data } = await api.get<JobResponse>(`/jobs/${jobId}`)
    console.log(`Job ${jobId} status:`, data)
    return data
  },

  // Health check
  health: async () => {
    const { data } = await api.get('/health')
    return data
  },
}

// Helper function to poll for job completion
export async function pollJobStatus(
  jobId: string,
  onProgress?: (status: string) => void
): Promise<QueryResponse> {
  const maxAttempts = 120 // 120 seconds max (2 minutes)
  let attempts = 0

  while (attempts < maxAttempts) {
    try {
      const job = await cagApi.getJobStatus(jobId)
      
      if (job.status === 'completed' && job.result) {
        return job.result
      }
      
      if (job.status === 'failed') {
        throw new Error(job.error || 'Query processing failed')
      }
      
      if (onProgress) {
        onProgress(job.status)
      }
    } catch (error) {
      console.error('Error polling job status:', error)
      // If it's a network error, throw immediately
      if (error instanceof AxiosError && !error.response) {
        throw new Error('Cannot connect to API. Please ensure the backend is running.')
      }
      throw error
    }
    
    // Wait 1 second before next poll
    await new Promise(resolve => setTimeout(resolve, 1000))
    attempts++
  }
  
  throw new Error('Query processing timeout after 2 minutes. The agents may be taking longer than expected.')
}
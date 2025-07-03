'use client'

import { useState } from 'react'
import { cagApi } from '@/lib/api'

export default function DebugPage() {
  const [status, setStatus] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const testHealth = async () => {
    setLoading(true)
    setStatus('Testing health endpoint...')
    try {
      const result = await cagApi.health()
      setStatus(`Health check passed: ${JSON.stringify(result, null, 2)}`)
    } catch (error) {
      setStatus(`Health check failed: ${error}`)
    }
    setLoading(false)
  }

  const testQuery = async () => {
    setLoading(true)
    setStatus('Testing query endpoint...')
    try {
      const result = await cagApi.query({
        query: 'What beers cost less than £6?'
      })
      setStatus(`Query successful: ${result.response.substring(0, 200)}...`)
    } catch (error) {
      setStatus(`Query failed: ${error}`)
    }
    setLoading(false)
  }

  const testAsyncQuery = async () => {
    setLoading(true)
    setStatus('Testing async query endpoint...')
    try {
      const { job_id } = await cagApi.queryAsync({
        query: 'What pizzas are under £12?'
      })
      setStatus(`Job created: ${job_id}\nPolling for results...`)
      
      // Poll manually to see what's happening
      let attempts = 0
      const pollInterval = setInterval(async () => {
        attempts++
        try {
          const job = await cagApi.getJobStatus(job_id)
          setStatus(`Job ${job_id}:\nStatus: ${job.status}\nAttempt: ${attempts}`)
          
          if (job.status === 'completed') {
            clearInterval(pollInterval)
            setStatus(`Job completed!\n${job.result?.response.substring(0, 200)}...`)
            setLoading(false)
          } else if (job.status === 'failed') {
            clearInterval(pollInterval)
            setStatus(`Job failed: ${job.error}`)
            setLoading(false)
          }
        } catch (error) {
          clearInterval(pollInterval)
          setStatus(`Polling error: ${error}`)
          setLoading(false)
        }
      }, 1000)
      
      // Stop after 30 seconds
      setTimeout(() => {
        clearInterval(pollInterval)
        if (loading) {
          setStatus('Timeout after 30 seconds')
          setLoading(false)
        }
      }, 30000)
    } catch (error) {
      setStatus(`Async query failed: ${error}`)
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">API Debug Page</h1>
      
      <div className="space-y-4">
        <div className="flex gap-4">
          <button
            onClick={testHealth}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
          >
            Test Health
          </button>
          
          <button
            onClick={testQuery}
            disabled={loading}
            className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
          >
            Test Sync Query
          </button>
          
          <button
            onClick={testAsyncQuery}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded disabled:opacity-50"
          >
            Test Async Query
          </button>
        </div>
        
        <div className="mt-8 p-4 bg-gray-100 rounded">
          <h2 className="font-bold mb-2">Status:</h2>
          <pre className="whitespace-pre-wrap">{status}</pre>
        </div>
        
        <div className="text-sm text-gray-600">
          <p>API URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
          <p>Open browser console for detailed logs</p>
        </div>
      </div>
    </div>
  )
}
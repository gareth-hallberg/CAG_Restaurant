'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Trash2, Loader2 } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import { cagApi, pollJobStatus } from '@/lib/api'
import MessageBubble from './MessageBubble'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  const {
    messages,
    sessionId,
    isLoading,
    addMessage,
    updateMessage,
    clearMessages,
    setLoading,
  } = useChatStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const query = input.trim()
    if (!query || isLoading) return
    
    // Clear input and focus
    setInput('')
    inputRef.current?.focus()
    
    // Add user message
    addMessage({
      role: 'user',
      content: query,
    })
    
    // Create a temporary ID for the assistant message
    const tempId = crypto.randomUUID()
    
    // Add assistant message placeholder with the ID we'll use to update it
    const assistantMessage = {
      id: tempId,
      role: 'assistant' as const,
      content: '',
      processing: true,
      timestamp: new Date(),
    }
    
    // Add to store directly to ensure we have the right ID
    useChatStore.setState((state) => ({
      messages: [...state.messages, assistantMessage],
    }))
    
    setLoading(true)
    
    try {
      // Use async API for better UX
      const { job_id } = await cagApi.queryAsync({
        query,
        session_id: sessionId,
      })
      
      // Poll for results
      const result = await pollJobStatus(job_id, (status) => {
        // Could update UI with status here
        console.log('Job status:', status)
      })
      
      // Update assistant message with response
      updateMessage(tempId, {
        content: result.response,
        processing: false,
      })
    } catch (error) {
      console.error('Query failed:', error)
      updateMessage(tempId, {
        content: error instanceof Error ? error.message : 'Sorry, something went wrong. Please try again.',
        processing: false,
        error: true,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-green-600 to-green-700 text-white p-4 shadow-lg">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Bella Terra Assistant</h1>
            <p className="text-green-100 text-sm">Context Augmented Generation Chat</p>
          </div>
          <button
            onClick={clearMessages}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
            disabled={isLoading || messages.length === 0}
          >
            <Trash2 size={18} />
            <span>Clear Chat</span>
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold text-gray-700 mb-4">
                Welcome to Bella Terra Assistant!
              </h2>
              <p className="text-gray-600 mb-8">
                Ask me anything about our menu, wines, or daily specials.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {[
                  "What pizzas do you have under £12?",
                  "Can you recommend a wine for pasta?",
                  "What are today's lunch specials?",
                  "Show me vegetarian options",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="text-left p-3 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t bg-gray-50 p-4">
        <div className="max-w-4xl mx-auto flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about our menu, wines, or specials..."
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </form>
    </div>
  )
}
import React from 'react'
import { format } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import { User, Bot, AlertCircle } from 'lucide-react'
import { Message } from '@/store/chatStore'
import clsx from 'clsx'

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  
  return (
    <div
      className={clsx(
        'flex gap-3 p-4 rounded-lg',
        isUser ? 'bg-blue-50' : 'bg-gray-50',
        message.error && 'bg-red-50'
      )}
    >
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <User size={18} className="text-white" />
          </div>
        ) : (
          <div className={clsx(
            "w-8 h-8 rounded-full flex items-center justify-center",
            message.error ? 'bg-red-500' : 'bg-gray-600'
          )}>
            {message.error ? (
              <AlertCircle size={18} className="text-white" />
            ) : (
              <Bot size={18} className="text-white" />
            )}
          </div>
        )}
      </div>
      
      <div className="flex-1 space-y-2">
        <div className="flex items-baseline gap-2">
          <span className="font-semibold text-sm">
            {isUser ? 'You' : 'Bella Terra Assistant'}
          </span>
          <span className="text-xs text-gray-500">
            {format(new Date(message.timestamp), 'HH:mm')}
          </span>
        </div>
        
        {message.processing ? (
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-gray-500">Analyzing menus and augmenting context...</span>
          </div>
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
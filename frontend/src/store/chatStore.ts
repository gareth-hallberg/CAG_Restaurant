import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  processing?: boolean
  error?: boolean
}

interface ChatState {
  messages: Message[]
  sessionId: string
  isLoading: boolean
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  clearMessages: () => void
  setLoading: (loading: boolean) => void
  generateSessionId: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      sessionId: crypto.randomUUID(),
      isLoading: false,
      
      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: crypto.randomUUID(),
              timestamp: new Date(),
            },
          ],
        })),
      
      updateMessage: (id, updates) =>
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg
          ),
        })),
      
      clearMessages: () =>
        set(() => ({
          messages: [],
          sessionId: crypto.randomUUID(),
        })),
      
      setLoading: (loading) => set({ isLoading: loading }),
      
      generateSessionId: () => set({ sessionId: crypto.randomUUID() }),
    }),
    {
      name: 'cag-chat-storage',
    }
  )
)
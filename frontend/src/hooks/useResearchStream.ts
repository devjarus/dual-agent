'use client'

import { useState, useCallback, useRef } from 'react'

export interface StreamMessage {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: Array<{ tool: string; args: any }>
  toolResults?: Array<{ result: any }>
}

export interface StreamEvent {
  type: 'text' | 'tool_use' | 'tool_result' | 'done' | 'error'
  chunk?: string
  tool?: string
  args?: any
  result?: any
  error?: string
}

export function useResearchStream() {
  const [messages, setMessages] = useState<StreamMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentMessage, setCurrentMessage] = useState<StreamMessage | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const startStream = useCallback(
    async (userId: string, message: string, sessionId?: string) => {
      setIsStreaming(true)

      // Add user message
      const userMessage: StreamMessage = { role: 'user', content: message }
      setMessages((prev) => [...prev, userMessage])

      // Initialize assistant message
      const assistantMessage: StreamMessage = {
        role: 'assistant',
        content: '',
        toolCalls: [],
        toolResults: [],
      }
      setCurrentMessage(assistantMessage)

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        // Create EventSource for SSE
        const url = new URL(`${apiUrl}/api/research/chat`)
        const params = new URLSearchParams({
          user_id: userId,
          message: message,
        })
        if (sessionId) {
          params.append('session_id', sessionId)
        }

        // Use POST with fetch for SSE
        const response = await fetch(`${apiUrl}/api/research/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userId,
            message: message,
            session_id: sessionId,
          }),
        })

        if (!response.body) {
          throw new Error('No response body')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()

          if (done) break

          // Decode chunk
          buffer += decoder.decode(value, { stream: true })

          // Process complete events
          const lines = buffer.split('\n\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.trim()) continue

            // Parse SSE format
            const eventMatch = line.match(/^event: (.+)/)
            const dataMatch = line.match(/^data: (.+)/)

            if (eventMatch && dataMatch) {
              const eventType = eventMatch[1]
              const eventData = JSON.parse(dataMatch[1]) as StreamEvent

              // Update current message based on event type
              setCurrentMessage((prev) => {
                if (!prev) return prev

                const updated = { ...prev }

                switch (eventData.type) {
                  case 'text':
                    updated.content += eventData.chunk || ''
                    break

                  case 'tool_use':
                    if (!updated.toolCalls) updated.toolCalls = []
                    updated.toolCalls.push({
                      tool: eventData.tool || '',
                      args: eventData.args,
                    })
                    break

                  case 'tool_result':
                    if (!updated.toolResults) updated.toolResults = []
                    updated.toolResults.push({
                      result: eventData.result,
                    })
                    break

                  case 'done':
                    // Finalize message
                    setMessages((prev) => [...prev, updated])
                    setCurrentMessage(null)
                    setIsStreaming(false)
                    break

                  case 'error':
                    console.error('Stream error:', eventData.error)
                    updated.content += `\n\n[Error: ${eventData.error}]`
                    setMessages((prev) => [...prev, updated])
                    setCurrentMessage(null)
                    setIsStreaming(false)
                    break
                }

                return updated
              })
            }
          }
        }
      } catch (error) {
        console.error('Stream error:', error)
        setIsStreaming(false)
        setCurrentMessage(null)
      }
    },
    []
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setCurrentMessage(null)
  }, [])

  return {
    messages,
    currentMessage,
    isStreaming,
    startStream,
    clearMessages,
  }
}

'use client'

import { useState } from 'react'
import { Send, Trash2, Loader2 } from 'lucide-react'
import { useResearchStream, StreamMessage } from '@/hooks/useResearchStream'
import { clsx } from 'clsx'

export default function ResearchPage() {
  const [input, setInput] = useState('')
  const [userId] = useState('user_demo') // TODO: Implement actual user management
  const { messages, currentMessage, isStreaming, startStream, clearMessages } =
    useResearchStream()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    const message = input.trim()
    setInput('')
    await startStream(userId, message)
  }

  const allMessages = currentMessage
    ? [...messages, currentMessage]
    : messages

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-12rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Research Agent</h1>
          <p className="text-muted-foreground mt-1">
            Ask questions and get AI-powered answers with tool use
          </p>
        </div>
        <button
          onClick={clearMessages}
          disabled={messages.length === 0}
          className={clsx(
            'flex items-center space-x-2 px-4 py-2 rounded-md transition-colors',
            messages.length === 0
              ? 'text-muted-foreground cursor-not-allowed'
              : 'text-destructive hover:bg-destructive/10'
          )}
        >
          <Trash2 className="h-4 w-4" />
          <span>Clear</span>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-card border rounded-lg p-6 mb-4 space-y-6">
        {allMessages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center">
            <div className="space-y-4">
              <div className="text-4xl">🤖</div>
              <div>
                <h2 className="text-xl font-semibold">
                  Start a conversation
                </h2>
                <p className="text-muted-foreground mt-2">
                  Ask me anything. I can search my knowledge base and recall
                  your preferences.
                </p>
              </div>
            </div>
          </div>
        ) : (
          allMessages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))
        )}

        {isStreaming && !currentMessage?.content && (
          <div className="flex items-center space-x-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Thinking...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={isStreaming}
          className={clsx(
            'flex-1 px-4 py-3 rounded-lg border bg-background',
            'focus:outline-none focus:ring-2 focus:ring-primary',
            isStreaming && 'opacity-50 cursor-not-allowed'
          )}
        />
        <button
          type="submit"
          disabled={!input.trim() || isStreaming}
          className={clsx(
            'px-6 py-3 rounded-lg flex items-center space-x-2 transition-colors',
            !input.trim() || isStreaming
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          )}
        >
          {isStreaming ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          <span>Send</span>
        </button>
      </form>
    </div>
  )
}

function MessageBubble({ message }: { message: StreamMessage }) {
  const isUser = message.role === 'user'

  return (
    <div
      className={clsx(
        'flex',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-[80%] rounded-lg px-4 py-3',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-foreground'
        )}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* Tool calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.toolCalls.map((call, idx) => (
              <div
                key={idx}
                className="text-xs bg-background/50 rounded px-2 py-1 font-mono"
              >
                🔧 {call.tool}({JSON.stringify(call.args)})
              </div>
            ))}
          </div>
        )}

        {/* Tool results */}
        {message.toolResults && message.toolResults.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.toolResults.map((result, idx) => (
              <div
                key={idx}
                className="text-xs bg-background/30 rounded px-2 py-1"
              >
                ✓ Result: {JSON.stringify(result.result).slice(0, 100)}...
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

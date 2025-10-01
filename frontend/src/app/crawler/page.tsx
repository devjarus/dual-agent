'use client'

import { useState } from 'react'
import { Globe, Play, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { useCrawlerStream } from '@/hooks/useCrawlerStream'
import { clsx } from 'clsx'

export default function CrawlerPage() {
  const [url, setUrl] = useState('')
  const [intent, setIntent] = useState('')
  const { status, pendingSteering, startCrawl, respondToSteering, reset } =
    useCrawlerStream()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim() || !intent.trim() || status.isActive) return

    await startCrawl(url.trim(), intent.trim())
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Crawler Agent</h1>
        <p className="text-muted-foreground mt-1">
          Intelligent web crawling with Ollama-powered link filtering
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-card border rounded-lg p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Starting URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/docs"
              disabled={status.isActive}
              className="w-full px-4 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Crawl Intent
            </label>
            <input
              type="text"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g., API documentation only"
              disabled={status.isActive}
              className="w-full px-4 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              required
            />
          </div>

          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={!url.trim() || !intent.trim() || status.isActive}
              className={clsx(
                'px-6 py-2 rounded-md flex items-center space-x-2 transition-colors',
                !url.trim() || !intent.trim() || status.isActive
                  ? 'bg-muted text-muted-foreground cursor-not-allowed'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              )}
            >
              {status.isActive ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              <span>Start Crawl</span>
            </button>

            {!status.isActive && status.events.length > 0 && (
              <button
                type="button"
                onClick={reset}
                className="px-6 py-2 rounded-md border hover:bg-muted transition-colors"
              >
                Reset
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Progress */}
      {status.events.length > 0 && (
        <div className="bg-card border rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Progress</h2>

          <div className="space-y-4">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Crawling...</span>
                <span>{Math.round(status.progress * 100)}%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${status.progress * 100}%` }}
                />
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 pt-2">
              <div className="text-center">
                <div className="text-2xl font-bold">{status.pagesVisited}</div>
                <div className="text-sm text-muted-foreground">
                  Pages Crawled
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{status.chunksStored}</div>
                <div className="text-sm text-muted-foreground">
                  Chunks Stored
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {status.isActive ? (
                    <Loader2 className="h-6 w-6 animate-spin inline-block" />
                  ) : (
                    <CheckCircle className="h-6 w-6 text-green-500 inline-block" />
                  )}
                </div>
                <div className="text-sm text-muted-foreground">Status</div>
              </div>
            </div>

            {/* Current URL */}
            {status.currentUrl && status.isActive && (
              <div className="text-sm text-muted-foreground">
                Currently crawling:{' '}
                <span className="font-mono">{status.currentUrl}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Steering Dialog */}
      {pendingSteering && (
        <div className="bg-card border border-primary rounded-lg p-6 mb-6">
          <div className="flex items-start space-x-3">
            <Globe className="h-5 w-5 text-primary mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold mb-2">User Steering Needed</h3>
              <p className="text-sm text-muted-foreground mb-3">
                {pendingSteering.reasoning}
              </p>
              <div className="bg-muted rounded px-3 py-2 mb-4">
                <div className="text-xs text-muted-foreground mb-1">Link:</div>
                <div className="font-mono text-sm break-all">
                  {pendingSteering.link}
                </div>
                <div className="text-xs text-muted-foreground mt-2">
                  Confidence: {Math.round((pendingSteering.confidence || 0) * 100)}%
                </div>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() =>
                    respondToSteering(true, pendingSteering.link || '')
                  }
                  className="flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  <CheckCircle className="h-4 w-4" />
                  <span>Approve</span>
                </button>
                <button
                  onClick={() =>
                    respondToSteering(false, pendingSteering.link || '')
                  }
                  className="flex items-center space-x-2 px-4 py-2 border rounded-md hover:bg-muted transition-colors"
                >
                  <XCircle className="h-4 w-4" />
                  <span>Reject</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Event Log */}
      {status.events.length > 0 && (
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Event Log</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {status.events.slice().reverse().map((event, idx) => (
              <div
                key={idx}
                className="text-sm font-mono bg-muted px-3 py-2 rounded"
              >
                <span className="text-muted-foreground">
                  [{event.type}]
                </span>{' '}
                {event.url || event.link || JSON.stringify(event)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

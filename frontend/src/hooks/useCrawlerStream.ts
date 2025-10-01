'use client'

import { useState, useCallback } from 'react'

export interface CrawlEvent {
  type: 'discovered' | 'crawling' | 'steering_needed' | 'stored' | 'completed' | 'error'
  url?: string
  progress?: number
  links?: string[]
  count?: number
  link?: string
  reasoning?: string
  confidence?: number
  waiting?: boolean
  chunks?: number
  total_pages?: number
  total_chunks?: number
  duration?: number
  error?: string
}

export interface CrawlStatus {
  isActive: boolean
  currentUrl?: string
  progress: number
  pagesVisited: number
  chunksStored: number
  events: CrawlEvent[]
}

export function useCrawlerStream() {
  const [status, setStatus] = useState<CrawlStatus>({
    isActive: false,
    progress: 0,
    pagesVisited: 0,
    chunksStored: 0,
    events: [],
  })
  const [pendingSteering, setPendingSteering] = useState<CrawlEvent | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  const startCrawl = useCallback(
    async (url: string, intent: string, maxDepth?: number, maxPages?: number) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        // Start crawl job
        const startResponse = await fetch(`${apiUrl}/api/crawler/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url,
            intent,
            max_depth: maxDepth,
            max_pages: maxPages,
          }),
        })

        if (!startResponse.ok) {
          throw new Error('Failed to start crawl')
        }

        const { job_id } = await startResponse.json()
        setJobId(job_id)

        // Initialize status
        setStatus({
          isActive: true,
          progress: 0,
          pagesVisited: 0,
          chunksStored: 0,
          events: [],
        })

        // Start streaming
        const streamResponse = await fetch(
          `${apiUrl}/api/crawler/jobs/${job_id}/stream`
        )

        if (!streamResponse.body) {
          throw new Error('No response body')
        }

        const reader = streamResponse.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()

          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete events
          const lines = buffer.split('\n\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.trim()) continue

            const eventMatch = line.match(/^event: (.+)/)
            const dataMatch = line.match(/^data: (.+)/)

            if (eventMatch && dataMatch) {
              const event = JSON.parse(dataMatch[1]) as CrawlEvent

              // Update status based on event
              setStatus((prev) => {
                const updated = { ...prev }
                updated.events = [...prev.events, event]

                switch (event.type) {
                  case 'crawling':
                    updated.currentUrl = event.url
                    updated.progress = event.progress || 0
                    break

                  case 'stored':
                    updated.pagesVisited += 1
                    updated.chunksStored += event.chunks || 0
                    break

                  case 'steering_needed':
                    setPendingSteering(event)
                    break

                  case 'completed':
                    updated.isActive = false
                    updated.pagesVisited = event.total_pages || updated.pagesVisited
                    updated.chunksStored = event.total_chunks || updated.chunksStored
                    updated.progress = 1.0
                    break

                  case 'error':
                    updated.isActive = false
                    console.error('Crawl error:', event.error)
                    break
                }

                return updated
              })
            }
          }
        }
      } catch (error) {
        console.error('Crawl stream error:', error)
        setStatus((prev) => ({ ...prev, isActive: false }))
      }
    },
    []
  )

  const respondToSteering = useCallback(
    async (approve: boolean, link: string) => {
      if (!jobId) return

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        await fetch(`${apiUrl}/api/crawler/jobs/${jobId}/steer`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approve, link }),
        })

        setPendingSteering(null)
      } catch (error) {
        console.error('Steering error:', error)
      }
    },
    [jobId]
  )

  const reset = useCallback(() => {
    setStatus({
      isActive: false,
      progress: 0,
      pagesVisited: 0,
      chunksStored: 0,
      events: [],
    })
    setPendingSteering(null)
    setJobId(null)
  }, [])

  return {
    status,
    pendingSteering,
    startCrawl,
    respondToSteering,
    reset,
  }
}

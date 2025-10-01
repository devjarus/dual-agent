'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Trash2, ExternalLink } from 'lucide-react'
import { clsx } from 'clsx'

interface KnowledgeEntry {
  id: string
  content: string
  url: string
  title: string
  domain: string
  chunk_index: number
  total_chunks: number
  crawl_date: string
  score?: number
}

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'search' | 'browse'>('search')
  const queryClient = useQueryClient()

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Search knowledge
  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['knowledge-search', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) return []

      const response = await fetch(`${apiUrl}/api/knowledge/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 20 }),
      })

      if (!response.ok) throw new Error('Search failed')
      return response.json() as Promise<KnowledgeEntry[]>
    },
    enabled: searchQuery.trim().length > 0,
  })

  // Browse all knowledge
  const { data: browseResults, isLoading: isBrowsing } = useQuery({
    queryKey: ['knowledge-browse'],
    queryFn: async () => {
      const response = await fetch(`${apiUrl}/api/knowledge/browse?limit=50`)
      if (!response.ok) throw new Error('Browse failed')
      return response.json() as Promise<KnowledgeEntry[]>
    },
    enabled: activeTab === 'browse',
  })

  // Delete knowledge
  const deleteMutation = useMutation({
    mutationFn: async (url: string) => {
      const response = await fetch(`${apiUrl}/api/knowledge/delete`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) throw new Error('Delete failed')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-browse'] })
      queryClient.invalidateQueries({ queryKey: ['knowledge-search'] })
    },
  })

  const results = activeTab === 'search' ? searchResults : browseResults
  const isLoading = activeTab === 'search' ? isSearching : isBrowsing

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Knowledge Explorer</h1>
        <p className="text-muted-foreground mt-1">
          Search and browse the global knowledge base
        </p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 border-b">
        <button
          onClick={() => setActiveTab('search')}
          className={clsx(
            'px-4 py-2 border-b-2 transition-colors',
            activeTab === 'search'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          )}
        >
          Search
        </button>
        <button
          onClick={() => setActiveTab('browse')}
          className={clsx(
            'px-4 py-2 border-b-2 transition-colors',
            activeTab === 'browse'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          )}
        >
          Browse All
        </button>
      </div>

      {/* Search Input */}
      {activeTab === 'search' && (
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search knowledge base..."
              className="w-full pl-10 pr-4 py-3 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      )}

      {/* Results */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">
            Loading...
          </div>
        ) : !results || results.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            {activeTab === 'search'
              ? 'No results found. Try a different search query.'
              : 'No knowledge entries found. Start crawling to add content.'}
          </div>
        ) : (
          results.map((entry) => (
            <div key={entry.id} className="bg-card border rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="font-semibold">{entry.title}</h3>
                    {entry.score && (
                      <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                        {Math.round(entry.score * 100)}% match
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
                    {entry.content}
                  </p>

                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <a
                      href={entry.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-1 hover:text-primary transition-colors"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>{entry.domain}</span>
                    </a>
                    <span>
                      Chunk {entry.chunk_index + 1} of {entry.total_chunks}
                    </span>
                    <span>{new Date(entry.crawl_date).toLocaleDateString()}</span>
                  </div>
                </div>

                <button
                  onClick={() => deleteMutation.mutate(entry.url)}
                  disabled={deleteMutation.isPending}
                  className="ml-4 p-2 text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                  title="Delete all chunks from this URL"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

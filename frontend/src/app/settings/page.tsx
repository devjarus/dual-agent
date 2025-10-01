'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, RotateCcw, CheckCircle } from 'lucide-react'
import { clsx } from 'clsx'

interface Config {
  anthropic: {
    model: string
    max_tokens: number
    temperature: number
  }
  ollama: {
    base_url: string
    embedding_model: string
    chat_model: string
    temperature: number
    timeout: number
  }
  crawler: {
    max_depth: number
    max_pages: number
    delay_between_requests: number
    respect_robots_txt: boolean
    timeout: number
    user_agent: string
  }
  vectordb: {
    persist_directory: string
    chunk_size: number
    chunk_overlap: number
  }
}

export default function SettingsPage() {
  const [editedConfig, setEditedConfig] = useState<Config | null>(null)
  const queryClient = useQueryClient()

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Fetch config
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const response = await fetch(`${apiUrl}/api/config`)
      if (!response.ok) throw new Error('Failed to fetch config')
      return response.json() as Promise<Config>
    },
  })

  // Update config
  const updateMutation = useMutation({
    mutationFn: async (updates: { section: string; updates: any }) => {
      const response = await fetch(`${apiUrl}/api/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      })

      if (!response.ok) throw new Error('Failed to update config')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      setEditedConfig(null)
    },
  })

  // Reset config
  const resetMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${apiUrl}/api/config/reset`, {
        method: 'POST',
      })

      if (!response.ok) throw new Error('Failed to reset config')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      setEditedConfig(null)
    },
  })

  const currentConfig = editedConfig || config

  const handleSave = (section: keyof Config) => {
    if (!editedConfig || !config) return

    const updates = editedConfig[section]
    updateMutation.mutate({ section, updates })
  }

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      resetMutation.mutate()
    }
  }

  if (isLoading) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        Loading configuration...
      </div>
    )
  }

  if (!currentConfig) {
    return (
      <div className="text-center py-12 text-destructive">
        Failed to load configuration
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure AgentX runtime settings
          </p>
        </div>
        <button
          onClick={handleReset}
          disabled={resetMutation.isPending}
          className="flex items-center space-x-2 px-4 py-2 border rounded-md hover:bg-muted transition-colors"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Reset to Defaults</span>
        </button>
      </div>

      {/* Crawler Settings */}
      <div className="bg-card border rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Crawler Settings</h2>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Max Depth (1-10)
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={currentConfig.crawler.max_depth}
                onChange={(e) =>
                  setEditedConfig({
                    ...currentConfig,
                    crawler: {
                      ...currentConfig.crawler,
                      max_depth: parseInt(e.target.value),
                    },
                  })
                }
                className="w-full px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Max Pages (1-1000)
              </label>
              <input
                type="number"
                min="1"
                max="1000"
                value={currentConfig.crawler.max_pages}
                onChange={(e) =>
                  setEditedConfig({
                    ...currentConfig,
                    crawler: {
                      ...currentConfig.crawler,
                      max_pages: parseInt(e.target.value),
                    },
                  })
                }
                className="w-full px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Delay Between Requests (seconds)
            </label>
            <input
              type="number"
              min="0.5"
              max="10"
              step="0.5"
              value={currentConfig.crawler.delay_between_requests}
              onChange={(e) =>
                setEditedConfig({
                  ...currentConfig,
                  crawler: {
                    ...currentConfig.crawler,
                    delay_between_requests: parseFloat(e.target.value),
                  },
                })
              }
              className="w-full px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="respect-robots"
              checked={currentConfig.crawler.respect_robots_txt}
              onChange={(e) =>
                setEditedConfig({
                  ...currentConfig,
                  crawler: {
                    ...currentConfig.crawler,
                    respect_robots_txt: e.target.checked,
                  },
                })
              }
              className="rounded border-gray-300"
            />
            <label htmlFor="respect-robots" className="text-sm font-medium">
              Respect robots.txt
            </label>
          </div>

          <button
            onClick={() => handleSave('crawler')}
            disabled={!editedConfig || updateMutation.isPending}
            className={clsx(
              'flex items-center space-x-2 px-4 py-2 rounded-md transition-colors',
              !editedConfig || updateMutation.isPending
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-primary text-primary-foreground hover:bg-primary/90'
            )}
          >
            <Save className="h-4 w-4" />
            <span>Save Crawler Settings</span>
          </button>
        </div>
      </div>

      {/* Vector DB Settings */}
      <div className="bg-card border rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Vector Database Settings</h2>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Chunk Size (128-2048)
              </label>
              <input
                type="number"
                min="128"
                max="2048"
                value={currentConfig.vectordb.chunk_size}
                onChange={(e) =>
                  setEditedConfig({
                    ...currentConfig,
                    vectordb: {
                      ...currentConfig.vectordb,
                      chunk_size: parseInt(e.target.value),
                    },
                  })
                }
                className="w-full px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Chunk Overlap
              </label>
              <input
                type="number"
                min="0"
                max="500"
                value={currentConfig.vectordb.chunk_overlap}
                onChange={(e) =>
                  setEditedConfig({
                    ...currentConfig,
                    vectordb: {
                      ...currentConfig.vectordb,
                      chunk_overlap: parseInt(e.target.value),
                    },
                  })
                }
                className="w-full px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <button
            onClick={() => handleSave('vectordb')}
            disabled={!editedConfig || updateMutation.isPending}
            className={clsx(
              'flex items-center space-x-2 px-4 py-2 rounded-md transition-colors',
              !editedConfig || updateMutation.isPending
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-primary text-primary-foreground hover:bg-primary/90'
            )}
          >
            <Save className="h-4 w-4" />
            <span>Save Vector DB Settings</span>
          </button>
        </div>
      </div>

      {/* Success Message */}
      {updateMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg p-4 flex items-center space-x-2">
          <CheckCircle className="h-5 w-5" />
          <span>Settings saved successfully</span>
        </div>
      )}
    </div>
  )
}

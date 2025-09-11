'use client'

import { useState, useEffect } from 'react'
import { KeywordInsertionSuggestion } from '../types'

interface KeywordInsertionProps {
  resumeId: string
  keywords: string[]
  onInsertionApplied: (bulletId: string, insertion: string) => void
}

export default function KeywordInsertion({ resumeId, keywords, onInsertionApplied }: KeywordInsertionProps) {
  const [suggestions, setSuggestions] = useState<KeywordInsertionSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateSuggestions = async () => {
    if (keywords.length === 0) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/structured-resume/${resumeId}/keyword-insertions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: resumeId,
          keywords: keywords,
          max_insertions_per_bullet: 2,
          max_chars_per_insertion: 25
        })
      })

      if (!response.ok) {
        throw new Error('Failed to generate keyword insertions')
      }

      const data = await response.json()
      setSuggestions(data.suggestions || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate suggestions')
    } finally {
      setIsLoading(false)
    }
  }

  const applyInsertion = (suggestion: KeywordInsertionSuggestion) => {
    onInsertionApplied(suggestion.bullet_id, suggestion.insertion_text)
    
    // Remove the applied suggestion
    setSuggestions(prev => prev.filter(s => s.bullet_id !== suggestion.bullet_id))
  }

  const dismissSuggestion = (bulletId: string) => {
    setSuggestions(prev => prev.filter(s => s.bullet_id !== bulletId))
  }

  useEffect(() => {
    if (keywords.length > 0) {
      generateSuggestions()
    }
  }, [keywords, resumeId])

  if (keywords.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Keyword Insertions</h3>
        <p className="text-sm text-gray-600">No keywords selected for insertion</p>
      </div>
    )
  }

  return (
    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-blue-900">Keyword Insertions</h3>
        <button
          onClick={generateSuggestions}
          disabled={isLoading}
          className="text-blue-600 hover:text-blue-800 text-sm disabled:opacity-50"
        >
          {isLoading ? 'Generating...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="text-red-600 text-sm mb-3">{error}</div>
      )}

      {isLoading && (
        <div className="text-blue-600 text-sm">Generating insertion suggestions...</div>
      )}

      {!isLoading && suggestions.length === 0 && !error && (
        <div className="text-gray-600 text-sm">
          No insertion suggestions available for the selected keywords.
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="space-y-3">
          {suggestions.map((suggestion, index) => (
            <div key={`${suggestion.bullet_id}-${index}`} className="bg-white rounded-lg p-3 border border-blue-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="text-sm text-gray-700 mb-2">
                    <span className="font-medium">Insert:</span> "{suggestion.insertion_text}"
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    Type: {suggestion.insertion_type} • Confidence: {Math.round(suggestion.confidence * 100)}%
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {suggestion.keywords_used.map((keyword, i) => (
                      <span key={i} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-3">
                  <button
                    onClick={() => applyInsertion(suggestion)}
                    className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700"
                  >
                    Apply
                  </button>
                  <button
                    onClick={() => dismissSuggestion(suggestion.bullet_id)}
                    className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs hover:bg-gray-300"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

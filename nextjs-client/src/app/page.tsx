'use client'

import { useState } from 'react'

interface KeywordItem {
  text: string
  priority: string
}

interface RecruiterBuckets {
  summary_headline_signals: KeywordItem[]
  core_requirements: KeywordItem[]
  methods_frameworks: KeywordItem[]
  tools_tech_stack: KeywordItem[]
  domain_platform_keywords: KeywordItem[]
  kpis_outcomes_metrics: KeywordItem[]
  leadership_scope_signals: KeywordItem[]
}

interface KeywordsResponse {
  recruiter_buckets: RecruiterBuckets
}

export default function Home() {
  const [jobText, setJobText] = useState('')
  const [maxTerms, setMaxTerms] = useState(30)
  const [results, setResults] = useState<KeywordsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExtractKeywords = async () => {
    if (!jobText.trim()) {
      setError('Please enter job description text')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await fetch('/api/keywords_text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_text: jobText,
          max_terms: maxTerms,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to extract keywords')
      }

      const data: KeywordsResponse = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const renderKeywordItem = (item: KeywordItem) => (
    <span 
      key={item.text} 
      className={`px-3 py-2 rounded-md text-sm font-medium border ${
        item.priority === 'must_have' 
          ? 'bg-red-100 text-red-800 border-red-200' 
          : 'bg-blue-100 text-blue-800 border-blue-200'
      }`}
    >
      {item.text}
      <span className={`ml-2 px-2 py-1 rounded text-xs ${
        item.priority === 'must_have' 
          ? 'bg-red-200 text-red-700' 
          : 'bg-blue-200 text-blue-700'
      }`}>
        {item.priority.replace('_', ' ')}
      </span>
    </span>
  )

  const renderBucket = (title: string, items: KeywordItem[], color: string, description: string) => (
    <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 border-l-${color}-500`}>
      <h3 className={`text-lg font-semibold mb-2 text-${color}-700`}>
        {title} ({items.length})
      </h3>
      <p className="text-sm text-gray-600 mb-4">{description}</p>
      {items.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {items.map(renderKeywordItem)}
        </div>
      ) : (
        <p className="text-gray-500 italic">No keywords found for this bucket</p>
      )}
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">Recruiter Keyword Extractor</h1>
      <p className="text-center text-gray-600 mb-8">Extract ATS-scannable keywords organized by recruiter search buckets</p>
      
      <div className="max-w-4xl mx-auto space-y-4 mb-8">
        <div>
          <label className="block text-sm font-medium mb-2">Job Description</label>
          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste job description here..."
            className="w-full h-32 p-3 border rounded-md"
          />
        </div>

        <div className="w-48">
          <label className="block text-sm font-medium mb-2">Max Terms</label>
          <input
            type="number"
            value={maxTerms}
            onChange={(e) => setMaxTerms(Number(e.target.value))}
            min="1"
            max="100"
            className="w-full p-2 border rounded-md"
          />
        </div>

        <button
          onClick={handleExtractKeywords}
          disabled={loading || !jobText.trim()}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-md disabled:opacity-50 font-medium"
        >
          {loading ? 'Extracting Keywords...' : 'Extract Keywords'}
        </button>

        {error && (
          <div className="p-3 bg-red-100 border border-red-300 rounded-md text-red-800">
            {error}
          </div>
        )}
      </div>

      {results && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold text-center">Recruiter Search Buckets</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {renderBucket(
              "Summary / Headline Signals", 
              results.recruiter_buckets.summary_headline_signals, 
              "green", 
              "What recruiters search to find profiles fast"
            )}
            
            {renderBucket(
              "Core Requirements", 
              results.recruiter_buckets.core_requirements, 
              "blue", 
              "Role-defining skills from Requirements/Qualifications"
            )}
            
            {renderBucket(
              "Methods & Frameworks", 
              results.recruiter_buckets.methods_frameworks, 
              "purple", 
              "Named ways of working that are searchable"
            )}
            
            {renderBucket(
              "Tools & Tech Stack", 
              results.recruiter_buckets.tools_tech_stack, 
              "orange", 
              "Systems and tools recruiters filter on in ATS"
            )}
            
            {renderBucket(
              "Domain / Platform Keywords", 
              results.recruiter_buckets.domain_platform_keywords, 
              "indigo", 
              "Industry or problem space terms"
            )}
            
            {renderBucket(
              "KPIs / Outcomes / Metrics", 
              results.recruiter_buckets.kpis_outcomes_metrics, 
              "pink", 
              "Quantifiable results recruiters scan for"
            )}
            
            {renderBucket(
              "Leadership & Scope Signals", 
              results.recruiter_buckets.leadership_scope_signals, 
              "teal", 
              "Level indicators recruiters query for when filtering seniors"
            )}
          </div>
        </div>
      )}
    </div>
  )
}

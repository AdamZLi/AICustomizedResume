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
  comparison?: {
    included: Array<{ text: string; positions: number[][]; match_type: string }>
    missing: Array<{ text: string }>
    coverage: { included: number; missing: number; percent: number }
  }
}

interface ResumeUploadResponse {
  resume_id: string
  filename: string
  message: string
}

export default function Home() {
  const [jobTitle, setJobTitle] = useState('Senior Product Manager')
  const [jobText, setJobText] = useState('')
  const [jdUrl, setJdUrl] = useState('')
  const [maxTerms, setMaxTerms] = useState(30)
  const [results, setResults] = useState<KeywordsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadedResume, setUploadedResume] = useState<ResumeUploadResponse | null>(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState<'included' | 'missing'>('included')
  const [rewriteLoading, setRewriteLoading] = useState(false)
  const [rewriteResult, setRewriteResult] = useState<string | null>(null)
  const [rewriteError, setRewriteError] = useState<string | null>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        setUploadError('Please select a PDF file')
        setSelectedFile(null)
        return
      }
      setSelectedFile(file)
      setUploadError(null)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploadLoading(true)
    setUploadError(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch('/api/upload_resume', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Upload failed')
      }

      const data: ResumeUploadResponse = await response.json()
      setUploadedResume(data)
      setSelectedFile(null)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploadLoading(false)
    }
  }

  const handleRewriteResume = async () => {
    if (!uploadedResume || selectedKeywords.length === 0) {
      setRewriteError('Please upload a resume and select keywords first')
      return
    }

    setRewriteLoading(true)
    setRewriteError(null)
    setRewriteResult(null)

    try {
      const response = await fetch('/api/resume/rewrite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_id: uploadedResume.resume_id,
          selected_keywords: selectedKeywords,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Rewrite failed')
      }

      const data = await response.json()
      // Extract resume_id from the URL and construct frontend API URL
      const resumeId = data.resume_id
      const downloadUrl = `/api/resume/${resumeId}/updated`
      setRewriteResult(downloadUrl)
    } catch (err) {
      setRewriteError(err instanceof Error ? err.message : 'Rewrite failed')
    } finally {
      setRewriteLoading(false)
    }
  }

  const handleExtractKeywords = async () => {
    if (!jdUrl.trim() && !jobText.trim()) {
      setError('Please enter either a job posting URL or paste job description text')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const endpoint = jdUrl ? '/api/keywords_url' : '/api/keywords_text'
      const body = jdUrl
        ? { 
            job_title: jobTitle, 
            job_url: jdUrl, 
            max_terms: maxTerms,
            ...(uploadedResume && { resume_id: uploadedResume.resume_id })
          }
        : { 
            job_text: jobText, 
            max_terms: maxTerms,
            ...(uploadedResume && { resume_id: uploadedResume.resume_id })
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to extract keywords')
      }

      const data: KeywordsResponse = await response.json()
      setResults(data)
      
      // Auto-select missing keywords for resume rewriting
      if (data.comparison && data.comparison.missing.length > 0) {
        const missingKeywords = data.comparison.missing.map(item => item.text)
        setSelectedKeywords(missingKeywords)
      }
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
      <h1 className="text-3xl font-bold mb-6 text-center">Resume Tailoring App</h1>
      <p className="text-center text-gray-600 mb-8">Upload your resume and extract keywords to tailor it perfectly</p>
      
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Resume Upload Section */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <div className="w-2 h-2 rounded-full bg-green-500 mr-3"></div>
              Resume Upload
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select PDF Resume</label>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileSelect}
                  className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">PDF files only, max 10MB</p>
              </div>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploadLoading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50 font-medium text-sm hover:bg-green-700 transition-colors"
              >
                {uploadLoading ? 'Uploading...' : 'Upload & Preview'}
              </button>
              {uploadError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {uploadError}
                </div>
              )}
              {uploadedResume && (
                <div className="space-y-3">
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                    ✅ Resume uploaded successfully: {uploadedResume.filename}
                  </div>
                  <button
                    onClick={() => setShowPreview(!showPreview)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    {showPreview ? '📄 Hide Preview' : '📄 Show Preview'}
                  </button>
                  
                  {showPreview && (
                    <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                        <h4 className="text-sm font-medium text-gray-700">Resume Preview</h4>
                      </div>
                      <div className="h-96">
                        <iframe
                          src={`/api/resume/${uploadedResume.resume_id}/pdf`}
                          className="w-full h-full"
                          title="Resume Preview"
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Keyword Extraction Section */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <div className="w-2 h-2 rounded-full bg-blue-500 mr-3"></div>
              Keyword Extraction
            </h2>
            <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Job Title (Optional but helpful)</label>
          <input
            type="text"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g., Senior Product Manager"
            className="w-full p-3 border rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Job Posting URL</label>
          <input
            type="url"
            value={jdUrl}
            onChange={(e) => setJdUrl(e.target.value)}
            placeholder="https://job-posting-url.com"
            className="w-full p-3 border rounded-md"
          />
          <p className="text-sm text-gray-500 mt-1">Or paste the job description text below</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Job Description Text (Fallback)</label>
          <input
            type="text"
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste job description here if URL doesn't work..."
            className="w-full p-3 border rounded-md"
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
          disabled={loading || (!jdUrl.trim() && !jobText.trim())}
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
          </div>
        </div>
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

      {/* Keyword Comparison Results */}
      {results && results.comparison && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Keyword Comparison Results</h3>
          
          {/* Coverage Stats */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{results.comparison.coverage.included}</div>
                <div className="text-sm text-gray-600">Included</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{results.comparison.coverage.missing}</div>
                <div className="text-sm text-gray-600">Missing</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{results.comparison.coverage.percent}%</div>
                <div className="text-sm text-gray-600">Coverage</div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 mb-4">
            <button
              onClick={() => setActiveTab('included')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'included'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Included ({results.comparison.included.length})
            </button>
            <button
              onClick={() => setActiveTab('missing')}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === 'missing'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Missing ({results.comparison.missing.length})
            </button>
          </div>

          {/* Keyword Lists */}
          <div className="space-y-4">
            {activeTab === 'included' && (
              <div className="flex flex-wrap gap-2">
                {results.comparison.included.map((item, index) => (
                  <span
                    key={index}
                    className="px-3 py-2 bg-green-100 text-green-800 text-sm rounded-full border border-green-300 font-medium"
                  >
                    {item.text}
                    <span className="ml-2 px-2 py-1 bg-green-200 text-green-700 rounded text-xs">
                      {item.match_type}
                    </span>
                  </span>
                ))}
              </div>
            )}
            
            {activeTab === 'missing' && (
              <div className="flex flex-wrap gap-2">
                {results.comparison.missing.map((item, index) => (
                  <span
                    key={index}
                    className="px-3 py-2 bg-red-100 text-red-800 text-sm rounded-full border border-red-300 font-medium"
                  >
                    {item.text}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Auto-selection Notice */}
          {results.comparison.missing.length > 0 && (
            <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <h4 className="text-sm font-medium text-orange-800 mb-2">
                🎯 Auto-selection Notice
              </h4>
              <p className="text-sm text-orange-700 mb-3">
                Missing keywords have been automatically selected for resume rewriting. You can clear them or modify the selection.
              </p>
              <div className="flex space-x-2">
                <button
                  onClick={() => setSelectedKeywords([])}
                  className="px-3 py-1 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 transition-colors"
                >
                  Clear All
                </button>
                <button
                  onClick={() => {
                    if (results.comparison) {
                      const missingKeywords = results.comparison.missing.map(item => item.text)
                      setSelectedKeywords(missingKeywords)
                    }
                  }}
                  className="px-3 py-1 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 transition-colors"
                >
                  Clear Auto-Selected
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Auto-selected Keywords Display */}
      {selectedKeywords.length > 0 && (
        <div className="mt-8 p-6 bg-orange-50 border border-orange-200 rounded-lg">
          <h3 className="text-lg font-semibold text-orange-800 mb-4">
            🎯 Auto-selected Missing Keywords ({selectedKeywords.length})
          </h3>
          <p className="text-sm text-orange-700 mb-4">
            These keywords were automatically selected because they were not found in your resume. 
            You can use them for resume rewriting.
          </p>
          <div className="flex flex-wrap gap-2">
            {selectedKeywords.map((keyword, index) => (
              <span
                key={index}
                className="px-3 py-2 bg-orange-100 text-orange-800 text-sm rounded-full border border-orange-300 font-medium cursor-pointer hover:bg-orange-200 transition-colors flex items-center"
                onClick={() => {
                  setSelectedKeywords(prev => prev.filter((_, i) => i !== index))
                }}
                title="Click to remove"
              >
                {keyword}
                <span className="ml-2 text-orange-600 hover:text-orange-800">×</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Rewrite Resume Section */}
      {uploadedResume && selectedKeywords.length > 0 && (
        <div className="mt-8 p-6 bg-white rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <div className="w-2 h-2 rounded-full bg-purple-500 mr-3"></div>
            Rewrite Resume with Keywords
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Rewrite your resume to include the selected keywords and improve your chances of passing ATS screening.
          </p>
          
          <button
            onClick={handleRewriteResume}
            disabled={rewriteLoading}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg disabled:opacity-50 font-medium hover:bg-purple-700 transition-colors"
          >
            {rewriteLoading ? '🔄 Rewriting Resume...' : '✏️ Rewrite Resume'}
          </button>

          {rewriteError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {typeof rewriteError === 'string' ? rewriteError : JSON.stringify(rewriteError)}
            </div>
          )}

          {rewriteResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="text-sm font-medium text-green-800 mb-2">✅ Resume Rewritten Successfully!</h4>
              <p className="text-sm text-green-700 mb-3">
                Your resume has been updated with the selected keywords.
              </p>
              <button
                onClick={async () => {
                  try {
                    const response = await fetch(rewriteResult)
                    if (!response.ok) {
                      throw new Error('Download failed')
                    }
                    const blob = await response.blob()
                    const url = window.URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = 'rewritten-resume.html'
                    document.body.appendChild(a)
                    a.click()
                    window.URL.revokeObjectURL(url)
                    document.body.removeChild(a)
                  } catch (error) {
                    console.error('Download error:', error)
                    alert('Download failed. Please try again.')
                  }
                }}
                className="inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
              >
                📄 Download Rewritten Resume
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

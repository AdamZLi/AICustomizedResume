'use client'

import { useState } from 'react'
import PreviewPanel from './components/PreviewPanel'

interface KeywordItem {
  text: string
  isSelected: boolean
  isAutoSelected?: boolean
}

interface ResumeRewriteResponse {
  resume_id: string
  updated_text: string
  change_log: Array<{
    section: string
    before: string
    after: string
    keywords_used: string[]
  }>
  included_keywords: string[]
  pdf_url: string
  original_text: string
  annotated_pdf_url?: string
  annotation_summary?: any
}

export default function Home() {
  // Resume state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadedResumeId, setUploadedResumeId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [resumeName, setResumeName] = useState<string>('')
  
  // Job details state
  const [jobTitle, setJobTitle] = useState('')
  const [jobUrl, setJobUrl] = useState('')
  const [showJdText, setShowJdText] = useState(false)
  const [jdText, setJdText] = useState('')
  const [isExtracting, setIsExtracting] = useState(false)
  
  // Keywords state
  const [keywords, setKeywords] = useState<KeywordItem[]>([])
  
  // Results state
  const [isProcessing, setIsProcessing] = useState(false)
  const [tailorResult, setTailorResult] = useState<ResumeRewriteResponse | null>(null)

  // Upload Resume
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    
    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      const response = await fetch('/api/upload_resume', {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        const result = await response.json()
        setUploadedResumeId(result.resume_id)
        setResumeName(selectedFile.name)
        setSelectedFile(null)
      }
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setIsUploading(false)
    }
  }

  // Extract Keywords
  const handleExtractKeywords = async () => {
    if (!uploadedResumeId || (!jobUrl && !jdText)) return
    
    setIsExtracting(true)
    try {
      const response = await fetch('/api/keywords_url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: uploadedResumeId,
          job_title: jobTitle,
          job_url: jobUrl,
          job_text: jdText,
          max_terms: 30
        }),
      })
      
      if (response.ok) {
        const result = await response.json()
        
        // Process keywords with auto-selection
        const allKeywords: string[] = []
        
        // Extract all keywords from recruiter buckets
        if (result.recruiter_buckets) {
          Object.values(result.recruiter_buckets).forEach((bucket: unknown) => {
            if (Array.isArray(bucket)) {
              bucket.forEach((item: { text?: string }) => {
                if (item.text && !allKeywords.includes(item.text)) {
                  allKeywords.push(item.text)
                }
              })
            }
          })
        }
        
        // Get included keywords from comparison
        const includedKeywords: string[] = []
        if (result.comparison && result.comparison.included) {
          result.comparison.included.forEach((item: { text?: string }) => {
            if (item.text && !includedKeywords.includes(item.text)) {
              includedKeywords.push(item.text)
            }
          })
        }
        
        const keywordItems: KeywordItem[] = allKeywords.map((keyword: string) => ({
          text: keyword,
          isSelected: !includedKeywords.includes(keyword), // Auto-select MISSING keywords (not included ones)
          isAutoSelected: !includedKeywords.includes(keyword) // Mark missing keywords as auto-selected
        }))
        
        setKeywords(keywordItems)
      }
    } catch (error) {
      console.error('Keyword extraction failed:', error)
    } finally {
      setIsExtracting(false)
    }
  }

  // Keywords Management
  const toggleKeyword = (index: number) => {
    setKeywords(prev => prev.map((kw, i) => 
      i === index ? { ...kw, isSelected: !kw.isSelected } : kw
    ))
  }

  const clearAll = () => {
    setKeywords(prev => prev.map(kw => ({ ...kw, isSelected: false })))
  }

  const clearAutoSelected = () => {
    setKeywords(prev => prev.map(kw => ({ 
      ...kw, 
      isSelected: kw.isSelected && !kw.isAutoSelected 
    })))
  }

  // Plan and Annotate Resume
  const handleTailorResume = async () => {
    if (!uploadedResumeId) return
    
    const selectedKeywords = keywords.filter(kw => kw.isSelected).map(kw => kw.text)
    if (selectedKeywords.length === 0) return
    
    console.log('Starting plan-and-annotate workflow...')
    console.log('Resume ID:', uploadedResumeId)
    console.log('Selected keywords:', selectedKeywords)
    console.log('Job title:', jobTitle)
    
    setIsProcessing(true)
    try {
      // Step 1: Generate Edit Plan
      console.log('Step 1: Generating edit plan...')
      const editPlanResponse = await fetch('/api/resume/edit-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: uploadedResumeId,
          selected_keywords: selectedKeywords,
          job_title: jobTitle
        }),
      })
      
      console.log('Edit plan response status:', editPlanResponse.status)
      if (!editPlanResponse.ok) {
        const errorText = await editPlanResponse.text()
        console.error('Edit plan error response:', errorText)
        throw new Error(`Failed to generate edit plan: ${editPlanResponse.status} - ${errorText}`)
      }
      
      const editPlanResult = await editPlanResponse.json()
      console.log('Edit plan generated:', editPlanResult)
      
      // Step 2: Apply Edit Plan
      console.log('Applying edit plan...')
      const applyPlanResponse = await fetch('/api/resume/apply-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: uploadedResumeId,
          edit_plan: editPlanResult.edit_plan,
          section_name: editPlanResult.section_name
        }),
      })
      
      console.log('Apply plan response status:', applyPlanResponse.status)
      if (!applyPlanResponse.ok) {
        const errorText = await applyPlanResponse.text()
        console.error('Apply plan error response:', errorText)
        throw new Error(`Failed to apply edit plan: ${applyPlanResponse.status} - ${errorText}`)
      }
      
      const applyPlanResult = await applyPlanResponse.json()
      console.log('Edit plan applied:', applyPlanResult)
      
      // Step 3: Create Annotated PDF
      console.log('Creating annotated PDF...')
      const formData = new FormData()
      formData.append('edit_plan', JSON.stringify(editPlanResult.edit_plan))
      formData.append('section_name', editPlanResult.section_name)
      
      const annotateResponse = await fetch(`/api/resume/${uploadedResumeId}/annotate`, {
        method: 'POST',
        body: formData,
      })
      
      console.log('Annotation response status:', annotateResponse.status)
      if (!annotateResponse.ok) {
        const errorText = await annotateResponse.text()
        console.error('Annotation error response:', errorText)
        throw new Error(`Failed to create annotated PDF: ${annotateResponse.status} - ${errorText}`)
      }
      
      const annotateResult = await annotateResponse.json()
      console.log('Annotated PDF created:', annotateResult)
      
      // Create result object compatible with existing UI
      const result = {
        resume_id: uploadedResumeId,
        updated_text: applyPlanResult.updated_lines.join('\n'),
        change_log: applyPlanResult.change_log,
        included_keywords: applyPlanResult.applied_keywords,
        pdf_url: annotateResult.annotated_pdf_url,
        original_text: editPlanResult.original_lines.join('\n'),
        annotated_pdf_url: annotateResult.annotated_pdf_url,
        annotation_summary: annotateResult.annotation_summary
      }
      
      setTailorResult(result)
      console.log('Plan-and-annotate workflow completed successfully!')
      
    } catch (error) {
      console.error('Plan-and-annotate workflow failed:', error)
      
      // Show more detailed error information
      let errorMessage = 'Failed to process resume. '
      if (error instanceof Error) {
        errorMessage += error.message
      } else if (typeof error === 'string') {
        errorMessage += error
      } else {
        errorMessage += 'Unknown error occurred'
      }
      
      console.error('Detailed error:', error)
      alert(errorMessage)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDownload = async () => {
    if (!tailorResult) return
    
    try {
      // Download the annotated PDF instead of HTML
      const response = await fetch(`/api/resume/${tailorResult.resume_id}/annotated.pdf`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'tailored-resume-annotated.pdf'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const selectedKeywords = keywords.filter(kw => kw.isSelected).map(kw => kw.text)
  const unselectedKeywords = keywords.filter(kw => !kw.isSelected).map(kw => kw.text)
  const coverage = keywords.length > 0 ? Math.round((selectedKeywords.length / keywords.length) * 100) : 0

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">Resume Tailor</h1>
          <p className="text-gray-600">Upload once, tailor for multiple job descriptions</p>
        </div>

        <div className="space-y-6">
          {/* Top Section - Input Areas */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Resume & Job Details */}
            <div className="lg:col-span-1 space-y-6">
              {/* Resume Upload */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Resume</h2>
                
                {!uploadedResumeId ? (
                  <div className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-xl p-6">
                      <input
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileSelect}
                        className="hidden"
                        id="file-upload"
                      />
                      <label htmlFor="file-upload" className="cursor-pointer">
                        <div className="text-center">
                          <div className="mx-auto w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                          </div>
                          <p className="text-sm text-gray-600">
                            {selectedFile ? selectedFile.name : 'Click to select PDF file'}
                          </p>
                        </div>
                      </label>
                    </div>
                    
                    <button
                      onClick={handleUpload}
                      disabled={!selectedFile || isUploading}
                      className="w-full bg-blue-600 text-white py-3 px-6 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isUploading ? 'Uploading...' : 'Upload Resume'}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-green-800">{resumeName}</p>
                          <p className="text-xs text-green-600">Ready for tailoring</p>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setUploadedResumeId(null)
                          setResumeName('')
                          setKeywords([])
                          setTailorResult(null)
                        }}
                        className="text-green-600 hover:text-green-800 text-sm"
                      >
                        Change
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Job Details - Compact Layout */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Job Details</h2>
                
                <div className="space-y-3">
                  {/* Job Title - Compact */}
                  <div className="flex items-center space-x-3">
                    <label className="text-sm font-medium text-gray-700 w-20 flex-shrink-0">
                      Job Title:
                    </label>
                    <input
                      type="text"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      placeholder="e.g., Senior Product Manager"
                      className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>
                  
                  {/* Job URL - Compact */}
                  <div className="flex items-center space-x-3">
                    <label className="text-sm font-medium text-gray-700 w-20 flex-shrink-0">
                      URL:
                    </label>
                    <input
                      type="url"
                      value={jobUrl}
                      onChange={(e) => setJobUrl(e.target.value)}
                      placeholder="https://job-posting-url.com"
                      className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    />
                  </div>
                  
                  {/* JD Text Toggle and Extract Button - Same Line */}
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => setShowJdText(!showJdText)}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      {showJdText ? 'Hide JD text' : 'Paste JD text instead'}
                    </button>
                    
                    <button
                      onClick={handleExtractKeywords}
                      disabled={!uploadedResumeId || (!jobUrl && !jdText) || isExtracting}
                      className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                    >
                      {isExtracting ? 'Extracting...' : 'Extract Keywords'}
                    </button>
                  </div>
                  
                  {/* JD Text Area - Conditional */}
                  {showJdText && (
                    <div className="flex items-start space-x-3">
                      <div className="w-20 flex-shrink-0"></div>
                      <textarea
                        value={jdText}
                        onChange={(e) => setJdText(e.target.value)}
                        placeholder="Paste job description here..."
                        rows={3}
                        className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Keywords */}
            <div className="lg:col-span-2">
              {keywords.length > 0 ? (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-semibold text-gray-900">Keywords</h2>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Coverage</p>
                        <p className="text-2xl font-bold text-blue-600">{coverage}%</p>
                      </div>
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${coverage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  
                  {/* Keyword Tabs */}
                  <div className="mb-6">
                    <div className="border-b border-gray-200">
                      <nav className="flex space-x-8">
                        <button className="py-2 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm">
                          Included ({selectedKeywords.length})
                        </button>
                        <button className="py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm">
                          Missing ({unselectedKeywords.length})
                        </button>
                      </nav>
                    </div>
                  </div>
                  
                  {/* Keywords Grid */}
                  <div className="mb-6">
                    <div className="flex flex-wrap gap-2">
                      {keywords.map((keyword, index) => (
                        <button
                          key={index}
                          onClick={() => toggleKeyword(index)}
                          className={`
                            px-3 py-1.5 rounded-full text-sm font-medium transition-colors
                            ${keyword.isSelected 
                              ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                              : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                            }
                            ${keyword.isAutoSelected ? 'ring-2 ring-yellow-400' : ''}
                          `}
                        >
                          {keyword.text}
                          {keyword.isAutoSelected && (
                            <span className="ml-1 text-yellow-600">•</span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center justify-between">
                    <div className="flex space-x-3">
                      <button
                        onClick={clearAll}
                        className="text-sm text-gray-600 hover:text-gray-800"
                      >
                        Clear All
                      </button>
                      <button
                        onClick={clearAutoSelected}
                        className="text-sm text-gray-600 hover:text-gray-800"
                      >
                        Clear Auto-Selected
                      </button>
                    </div>
                    
                    <button
                                              onClick={handleTailorResume}
                      disabled={selectedKeywords.length === 0 || isProcessing}
                      className="bg-blue-600 text-white py-2 px-6 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                                              {isProcessing ? 'Processing...' : 'Tailor Resume'}
                    </button>
                  </div>
                </div>
              ) : uploadedResumeId ? (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <div className="text-center py-12">
                    <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-6">
                      <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">Ready to Extract Keywords</h2>
                    <p className="text-gray-600 mb-6">Enter job details on the left to analyze keywords and see how well your resume matches</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                          <span className="text-sm font-medium text-blue-600">1</span>
                        </div>
                        <p className="text-sm text-gray-700">Enter job title & URL</p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                          <span className="text-sm font-medium text-blue-600">2</span>
                        </div>
                        <p className="text-sm text-gray-700">Extract keywords</p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                          <span className="text-sm font-medium text-blue-600">3</span>
                        </div>
                        <p className="text-sm text-gray-700">Review & tailor</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <div className="text-center py-12">
                    <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">Upload Your Resume First</h2>
                    <p className="text-gray-600 mb-8">Start by uploading your PDF resume on the left to begin tailoring it for job applications</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
                      <div className="text-center">
                        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                        </div>
                        <h3 className="text-sm font-medium text-gray-900 mb-1">Upload Resume</h3>
                        <p className="text-xs text-gray-500">PDF format, max 10MB</p>
                      </div>
                      <div className="text-center">
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                        </div>
                        <h3 className="text-sm font-medium text-gray-500 mb-1">Extract Keywords</h3>
                        <p className="text-xs text-gray-400">From job description</p>
                      </div>
                      <div className="text-center">
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </div>
                        <h3 className="text-sm font-medium text-gray-500 mb-1">Tailor Resume</h3>
                        <p className="text-xs text-gray-400">With selected keywords</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Bottom Section - Results */}
          {tailorResult && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Results</h2>
                <button
                  onClick={handleDownload}
                  className="bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  Download PDF
                </button>
              </div>
              
                                  <PreviewPanel
                                      originalText={tailorResult.original_text}
                updatedText={tailorResult.updated_text}
                includedKeywords={tailorResult.included_keywords}
                resumeId={tailorResult.resume_id}
                    />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

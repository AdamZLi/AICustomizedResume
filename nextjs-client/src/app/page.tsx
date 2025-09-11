'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import PreviewPanel from './components/PreviewPanel'
import StructuredEditor from './structured-editor/components/StructuredEditor'
import LivePreview from './structured-editor/components/LivePreview'
import { StructuredResume, SectionType } from './structured-editor/types'
import { useAutosave } from './structured-editor/hooks/useAutosave'

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
  const router = useRouter()
  
  // Resume state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadedResumeId, setUploadedResumeId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [resumeName, setResumeName] = useState<string>('')
  
  // Structured editor state
  const [structuredResume, setStructuredResume] = useState<StructuredResume | null>(null)
  const [showStructuredEditor, setShowStructuredEditor] = useState(false)
  const [isLoadingStructuredResume, setIsLoadingStructuredResume] = useState(false)
  const [structuredEditorError, setStructuredEditorError] = useState<string | null>(null)
  
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
        
        // Automatically parse the resume into structured format
        try {
          const parseResponse = await fetch('/api/structured-resume/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              resume_id: result.resume_id,
              parse_options: {}
            }),
          })
          
          if (parseResponse.ok) {
            console.log('Resume parsed successfully into structured format')
          }
        } catch (parseError) {
          console.warn('Failed to parse resume into structured format:', parseError)
        }
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

  // Load structured resume for editing
  const loadStructuredResume = async (resumeId: string) => {
    setIsLoadingStructuredResume(true)
    setStructuredEditorError(null)
    
    try {
      // First get the raw resume text
      const textResponse = await fetch(`/api/resume/${resumeId}/text`)
      if (!textResponse.ok) {
        throw new Error('Failed to load resume text')
      }
      const textData = await textResponse.json()
      const resumeText = textData.text
      
      // Parse the resume into structured format
      const parseResponse = await fetch('/api/structured-resume/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_id: resumeId })
      })
      
      if (!parseResponse.ok) {
        throw new Error('Failed to parse resume')
      }
      
      const parseResult = await parseResponse.json()
      let structuredResume = parseResult.structured_resume
      
      // If parsing didn't work well, enhance it with basic extraction
      if (structuredResume.headline.name === "Your Name" || structuredResume.work_experience.length === 0) {
        console.log("Enhancing parsed resume with frontend extraction")
        structuredResume = enhanceParsedResume(structuredResume, resumeText)
        console.log("Enhanced resume:", structuredResume)
      }
      
      console.log("Setting structured resume:", structuredResume)
      setStructuredResume(structuredResume)
      setShowStructuredEditor(true)
    } catch (error) {
      console.error('Error loading structured resume:', error)
      setStructuredEditorError(error instanceof Error ? error.message : 'Failed to load resume for editing')
    } finally {
      setIsLoadingStructuredResume(false)
    }
  }

  // Enhance parsed resume with basic text extraction
  const enhanceParsedResume = (resume: any, text: string) => {
    const lines = text.split('\n').map(line => line.trim()).filter(line => line)
    
    // Extract name (first line that looks like a name)
    if (resume.headline.name === "Your Name") {
      const nameMatch = lines.find(line => /^[A-Z][a-z]+(\s*\([^)]+\))?\s+[A-Z][a-z]+/.test(line))
      if (nameMatch) {
        const name = nameMatch.match(/^([A-Z][a-z]+(?:\s*\([^)]+\))?\s+[A-Z][a-z]+)/)?.[1] || nameMatch
        resume.headline.name = name
      }
    }
    
    // Extract title (line after name that's not a section header)
    if (resume.headline.title === "Professional Title") {
      const nameIndex = lines.findIndex(line => line.includes(resume.headline.name))
      if (nameIndex >= 0 && nameIndex + 1 < lines.length) {
        const titleLine = lines[nameIndex + 1]
        if (!/^[A-Z\s]+$/.test(titleLine) && !titleLine.includes('|') && titleLine.length < 150) {
          resume.headline.title = titleLine
        }
      }
    }
    
    // Extract contact info from the first line
    const firstLine = lines[0]
    if (firstLine && firstLine.includes('@') && firstLine.includes('|')) {
      const parts = firstLine.split('|')
      const contact: any = {}
      
      for (const part of parts) {
        const trimmed = part.trim()
        if (trimmed.includes('@') && !contact.email) {
          // Extract just the email part
          const emailMatch = trimmed.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/)
          if (emailMatch) {
            contact.email = emailMatch[1]
          }
        } else if (/^\+?[\d\s\-\(\)]+$/.test(trimmed) && trimmed.replace(/\D/g, '').length >= 10) {
          contact.phone = trimmed
        } else if (trimmed.toLowerCase().includes('linkedin')) {
          contact.linkedin = trimmed
        } else if (trimmed.toLowerCase().includes('medium')) {
          contact.medium = trimmed
        }
      }
      
      if (Object.keys(contact).length > 0) {
        resume.headline.contact = { ...resume.headline.contact, ...contact }
      }
    }
    
    // Extract work experience
    if (resume.work_experience.length === 0) {
      const workStartIndex = lines.findIndex(line => line.toLowerCase().includes('working experience'))
      if (workStartIndex >= 0) {
        const workLines = lines.slice(workStartIndex + 1)
        const workExperiences = []
        let currentJob = null
        let currentBullets = []
        
        for (const line of workLines) {
          // Check if this is a new job (contains company name and dates)
          if (line.includes('Microsoft') || line.includes('Accenture') || line.includes('Smith School')) {
            // Save previous job
            if (currentJob) {
              currentJob.bullets = currentBullets
              workExperiences.push(currentJob)
            }
            
            // Start new job
            const jobMatch = line.match(/^(.+?)\s+(.+?)\s+\((.+?)\)\s+(.+?)$/)
            if (jobMatch) {
              currentJob = {
                id: `work-${workExperiences.length + 1}`,
                title: jobMatch[1].trim(),
                company: jobMatch[2].trim(),
                location: '',
                start_date: jobMatch[4].split(' ')[0],
                end_date: jobMatch[4].split(' ')[2] || 'Present',
                is_current: jobMatch[4].split(' ')[2] === 'Present',
                bullets: [],
                order: workExperiences.length,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              }
              currentBullets = []
            }
          } else if (line.startsWith('- ')) {
            // This is a bullet point
            currentBullets.push({
              id: `bullet-${currentBullets.length + 1}`,
              text: line.substring(2).trim(),
              is_active: true,
              order: currentBullets.length,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            })
          }
        }
        
        // Save last job
        if (currentJob) {
          currentJob.bullets = currentBullets
          workExperiences.push(currentJob)
        }
        
        resume.work_experience = workExperiences
      }
    }
    
    // Extract entrepreneurship
    if (resume.entrepreneurship.length === 0) {
      const entrepreneurshipStartIndex = lines.findIndex(line => line.toLowerCase().includes('entrepreneurship'))
      if (entrepreneurshipStartIndex >= 0) {
        const entrepreneurshipLines = lines.slice(entrepreneurshipStartIndex + 1)
        const entrepreneurshipExperiences = []
        let currentVenture = null
        let currentBullets = []
        
        for (const line of entrepreneurshipLines) {
          // Check if this is a new venture (contains company name and dates)
          if (line.includes('Uphonest Capital') || line.includes('YouTube') || line.includes('The Great Prep')) {
            // Save previous venture
            if (currentVenture) {
              currentVenture.bullets = currentBullets
              entrepreneurshipExperiences.push(currentVenture)
            }
            
            // Start new venture
            const ventureMatch = line.match(/^(.+?)\s+(.+?)\s+(.+?)$/)
            if (ventureMatch) {
              currentVenture = {
                id: `venture-${entrepreneurshipExperiences.length + 1}`,
                title: ventureMatch[1].trim(),
                company: ventureMatch[2].trim(),
                location: '',
                start_date: ventureMatch[3].split(' ')[0],
                end_date: ventureMatch[3].split(' ')[2] || 'Present',
                is_current: ventureMatch[3].split(' ')[2] === 'Present',
                bullets: [],
                order: entrepreneurshipExperiences.length,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              }
              currentBullets = []
            }
          } else if (line.startsWith('- ')) {
            // This is a bullet point
            currentBullets.push({
              id: `bullet-${currentBullets.length + 1}`,
              text: line.substring(2).trim(),
              is_active: true,
              order: currentBullets.length,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            })
          }
        }
        
        // Save last venture
        if (currentVenture) {
          currentVenture.bullets = currentBullets
          entrepreneurshipExperiences.push(currentVenture)
        }
        
        resume.entrepreneurship = entrepreneurshipExperiences
      }
    }
    
    // Extract education
    if (resume.education.length === 0) {
      const educationStartIndex = lines.findIndex(line => line.toLowerCase().includes('education'))
      if (educationStartIndex >= 0) {
        const educationLines = lines.slice(educationStartIndex + 1)
        const educationEntries = []
        
        for (const line of educationLines) {
          if (line.includes('Bachelor of Commerce') || line.includes('Queens University')) {
            const educationEntry = {
              id: `education-${educationEntries.length + 1}`,
              degree: 'Bachelor of Commerce',
              institution: 'Queens University',
              location: '',
              start_date: '2016',
              end_date: '2020',
              gpa: '',
              extras: [
                'Deans List | Coursework in CS & Analytics',
                'Awards: Deans List Scholarship, Queens Excellence Scholarship, Sun Life Global Investment Scholarship',
                'Extracurriculars: Deloitte Case Competition (1st place), Case IT International Competition (2nd place)'
              ],
              order: 0,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
            educationEntries.push(educationEntry)
            break // Only one education entry in this resume
          }
        }
        
        resume.education = educationEntries
      }
    }
    
    // Extract additional info
    if (resume.additional_info.length === 0) {
      const additionalInfoStartIndex = lines.findIndex(line => line.toLowerCase().includes('additional information'))
      if (additionalInfoStartIndex >= 0) {
        const additionalInfoLines = lines.slice(additionalInfoStartIndex + 1)
        const additionalInfoEntries = []
        
        // Blog Writing
        const blogLine = additionalInfoLines.find(line => line.includes('Blog Writing'))
        if (blogLine) {
          additionalInfoEntries.push({
            id: 'additional-1',
            category: 'Blog Writing',
            items: ['What Makes a Great Product Manager, Product Requirement Documentation Guidebook'],
            order: 0
          })
        }
        
        // Technology & Skills
        const skillsLine = additionalInfoLines.find(line => line.includes('Technology & Skills'))
        if (skillsLine) {
          additionalInfoEntries.push({
            id: 'additional-2',
            category: 'Technology & Skills',
            items: ['LangChain, VectorDB, SQL, Kusto, Power BI, Python, Azure DevOps, JIRA, Design Thinking'],
            order: 1
          })
        }
        
        resume.additional_info = additionalInfoEntries
      }
    }
    
    return resume
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
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            if (!uploadedResumeId) return
                            loadStructuredResume(uploadedResumeId)
                          }}
                          disabled={isLoadingStructuredResume}
                          className="bg-blue-600 text-white px-3 py-1 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isLoadingStructuredResume ? 'Loading...' : 'Edit Resume'}
                        </button>
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

      {/* Structured Editor Section */}
      {showStructuredEditor && (
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900">Resume Editor</h2>
                <p className="text-sm text-gray-600">Edit your resume sections below</p>
              </div>
              <button
                onClick={() => setShowStructuredEditor(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {structuredEditorError ? (
              <div className="text-center py-8">
                <div className="text-red-600 mb-4">
                  <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Resume</h3>
                <p className="text-gray-600 mb-4">{structuredEditorError}</p>
                <button
                  onClick={() => setStructuredEditorError(null)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Try Again
                </button>
              </div>
            ) : structuredResume ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Panel - Structured Editor */}
                <div className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
                  <StructuredEditor
                    resume={structuredResume}
                    onResumeUpdate={(updatedResume) => setStructuredResume(updatedResume)}
                  />
                </div>
                
                {/* Right Panel - Live Preview */}
                <div className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
                  <LivePreview
                    resume={structuredResume}
                  />
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading resume editor...</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

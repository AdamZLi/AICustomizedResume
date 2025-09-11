'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import StructuredEditor from './components/StructuredEditor'
import LivePreview from './components/LivePreview'
import { StructuredResume, SectionType } from './types'
import { useAutosave } from './hooks/useAutosave'

function StructuredEditorContent() {
  const router = useRouter()
  const [resumeId, setResumeId] = useState<string | null>(null)
  
  // Get resumeId from URL params after component mounts
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search)
      const id = urlParams.get('resumeId')
      console.log('Setting resumeId from URL:', id)
      setResumeId(id)
    }
  }, [])
  
  const [resume, setResume] = useState<StructuredResume | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // Load resume data
  useEffect(() => {
    console.log('ResumeId from URL:', resumeId)
    if (resumeId) {
      loadResume(resumeId)
    } else {
      console.log('No resumeId found in URL')
    }
  }, [resumeId])

  const loadResume = async (id: string) => {
    console.log('Loading resume with ID:', id)
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/structured-resume/${id}`)
      console.log('Response status:', response.status)
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Response error:', errorText)
        throw new Error(`Failed to load resume: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Loaded resume data:', data)
      setResume(data.resume)
    } catch (err) {
      console.error('Load resume error:', err)
      setError(err instanceof Error ? err.message : 'Failed to load resume')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResumeUpdate = useCallback((updatedResume: StructuredResume) => {
    setResume(prevResume => {
      // Only update if the resume actually changed
      if (JSON.stringify(prevResume) === JSON.stringify(updatedResume)) {
        return prevResume
      }
      return updatedResume
    })
    setHasUnsavedChanges(true)
  }, [])

  // Autosave functionality
  const { save: autosave, isSaving } = useAutosave(resume, {
    delay: 800,
    onSave: async (data) => {
      if (!resumeId || !data || !data.headline) return
      
      try {
        // Save each section that has been modified
        const response = await fetch(`/api/structured-resume/${resumeId}/section`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resume_id: resumeId,
            section_type: SectionType.HEADLINE,
            section_data: data.headline
          })
        })
        
        if (!response.ok) {
          throw new Error('Failed to save resume')
        }
        
        setHasUnsavedChanges(false)
      } catch (err) {
        console.error('Autosave failed:', err)
        throw err
      }
    },
    onError: (error) => {
      console.error('Autosave error:', error)
    }
  })

  const handleSave = async () => {
    if (!resume || !resumeId) return
    
    try {
      // Save each section that has been modified
      // This is a simplified version - in a real app, you'd track which sections changed
      const response = await fetch(`/api/structured-resume/${resumeId}/section`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: resumeId,
          section_type: SectionType.HEADLINE,
          section_data: resume.headline
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to save resume')
      }
      
      setHasUnsavedChanges(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save resume')
    }
  }

  const handleExport = async (format: string) => {
    if (!resumeId) return
    
    try {
      const response = await fetch(`/api/structured-resume/${resumeId}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: resumeId,
          format: format,
          include_annotations: false
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to export resume')
      }
      
      // Download the file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `resume-${resumeId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export resume')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading resume...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Resume</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  if (!resume) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Resume Not Found</h2>
          <p className="text-gray-600 mb-4">The requested resume could not be found.</p>
          <p className="text-sm text-gray-500 mb-4">ResumeId: {resumeId || 'null'}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/')}
                className="text-gray-600 hover:text-gray-900"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">Resume Editor</h1>
                <p className="text-sm text-gray-600">{resume.original_filename}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {isSaving && (
                <span className="text-sm text-blue-600 flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                  Saving...
                </span>
              )}
              {hasUnsavedChanges && !isSaving && (
                <span className="text-sm text-orange-600">Unsaved changes</span>
              )}
              {!hasUnsavedChanges && !isSaving && (
                <span className="text-sm text-green-600">Saved</span>
              )}
              
              <button
                onClick={handleSave}
                disabled={!hasUnsavedChanges || isSaving}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save
              </button>
              
              <div className="relative">
                <button
                  onClick={() => handleExport('pdf')}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                >
                  Export PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-120px)]">
          {/* Left Panel - Structured Editor */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <StructuredEditor
              resume={resume}
              onResumeUpdate={handleResumeUpdate}
            />
          </div>
          
          {/* Right Panel - Live Preview */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <LivePreview
              resume={resume}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default function StructuredEditorPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    }>
      <StructuredEditorContent />
    </Suspense>
  )
}

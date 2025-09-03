'use client'

import { useState, useRef, useEffect } from 'react'

interface PreviewPanelProps {
  originalText: string
  updatedText: string
  includedKeywords: string[]
  resumeId: string
}

type PreviewMode = 'clean' | 'diff' | 'keywords'

export default function PreviewPanel({ 
  originalText, 
  updatedText, 
  includedKeywords, 
  resumeId 
}: PreviewPanelProps) {
  const [activeMode, setActiveMode] = useState<PreviewMode>('clean')
  const [diffView, setDiffView] = useState<'split' | 'unified'>('split')
  const textRef = useRef<HTMLDivElement>(null)

  // Custom diff function
  const createDiff = (original: string, updated: string) => {
    const originalLines = original.split('\n')
    const updatedLines = updated.split('\n')
    const diff: Array<{ type: 'added' | 'removed' | 'unchanged', line: string, lineNumber?: number }> = []
    
    let i = 0, j = 0
    while (i < originalLines.length || j < updatedLines.length) {
      if (i < originalLines.length && j < updatedLines.length && originalLines[i] === updatedLines[j]) {
        diff.push({ type: 'unchanged', line: originalLines[i], lineNumber: i + 1 })
        i++
        j++
      } else if (j < updatedLines.length && (i >= originalLines.length || originalLines[i] !== updatedLines[j])) {
        diff.push({ type: 'added', line: updatedLines[j], lineNumber: j + 1 })
        j++
      } else if (i < originalLines.length) {
        diff.push({ type: 'removed', line: originalLines[i], lineNumber: i + 1 })
        i++
      }
    }
    return diff
  }

  // Keyword highlighting effect
  useEffect(() => {
    if (activeMode === 'keywords' && textRef.current && includedKeywords.length > 0) {
      const element = textRef.current
      const text = element.innerHTML
      
      // Simple regex-based highlighting
      let highlightedText = text
      includedKeywords.forEach(keyword => {
        const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
        highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>')
      })
      
      element.innerHTML = highlightedText
    }
  }, [activeMode, includedKeywords, updatedText])

  const renderCleanMode = () => (
    <div className="space-y-8">
      {/* Updated Text with Minimal Edits */}
      <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Updated Resume (Minimal Edits)</h3>
        <div className="prose prose-sm max-w-none">
          {updatedText.split('\n\n').map((paragraph, index) => (
            <p key={index} className="mb-4 text-gray-700 leading-relaxed">
              {paragraph}
            </p>
          ))}
        </div>
      </div>

      {/* Annotated PDF Preview */}
      <div className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
        <h3 className="text-lg font-semibold text-gray-900 p-6 pb-0">Annotated PDF Preview</h3>
        <iframe 
          src={`/api/resume/${resumeId}/annotated.pdf`}
          className="w-full h-96 border-0"
          title="Annotated Resume PDF Preview"
        />
      </div>
    </div>
  )

  const renderDiffMode = () => {
    const diff = createDiff(originalText, updatedText)
    
    return (
      <div className="space-y-6">
        {/* Diff Controls */}
        <div className="flex space-x-2">
          <button
            onClick={() => setDiffView('split')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              diffView === 'split' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Split View
          </button>
          <button
            onClick={() => setDiffView('unified')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              diffView === 'unified' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Unified View
          </button>
        </div>

        {/* Diff Content */}
        <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Changes</h3>
          <div className="font-mono text-sm space-y-1">
            {diff.map((item, index) => (
              <div key={index} className={`p-2 rounded ${
                item.type === 'added' ? 'bg-green-50 text-green-800' :
                item.type === 'removed' ? 'bg-red-50 text-red-800' :
                'bg-gray-50 text-gray-600'
              }`}>
                <span className="mr-2">
                  {item.type === 'added' ? '+' : item.type === 'removed' ? '-' : ' '}
                </span>
                {item.line}
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderKeywordsMode = () => (
    <div className="space-y-6">
      {/* Keywords Legend */}
      <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Included Keywords</h3>
        <div className="flex flex-wrap gap-2">
          {includedKeywords.map((keyword, index) => (
            <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
              {keyword}
            </span>
          ))}
        </div>
      </div>

      {/* Highlighted Text */}
      <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Keywords Highlighted</h3>
        <div 
          ref={textRef}
          className="prose prose-sm max-w-none text-gray-700 leading-relaxed"
        >
          {updatedText.split('\n\n').map((paragraph, index) => (
            <p key={index} className="mb-4">
              {paragraph}
            </p>
          ))}
        </div>
      </div>
    </div>
  )

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100">
      {/* Mode Tabs */}
      <div className="px-8 py-6 border-b border-gray-100">
        <div className="flex space-x-1">
          {[
            { id: 'clean' as PreviewMode, label: 'Updated Text' },
            { id: 'diff' as PreviewMode, label: 'Changes' },
            { id: 'keywords' as PreviewMode, label: 'Keywords' }
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setActiveMode(mode.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeMode === mode.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="px-8 py-6">
        {activeMode === 'clean' && renderCleanMode()}
        {activeMode === 'diff' && renderDiffMode()}
        {activeMode === 'keywords' && renderKeywordsMode()}
      </div>
    </div>
  )
}

'use client'

import { useState, useCallback } from 'react'
import { Education } from '../types'

interface EducationEditorProps {
  education: Education[]
  onUpdate: (education: Education[]) => void
}

export default function EducationEditor({ education, onUpdate }: EducationEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null)

  const addEducation = useCallback(() => {
    const newEducation: Education = {
      id: `edu_${Date.now()}`,
      institution: '',
      degree: '',
      location: '',
      start_date: '',
      end_date: '',
      gpa: '',
      extras: [],
      order: education.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    onUpdate([...education, newEducation])
    setEditingId(newEducation.id)
  }, [education, onUpdate])

  const updateEducation = useCallback((id: string, updates: Partial<Education>) => {
    const updated = education.map(edu => 
      edu.id === id ? { ...edu, ...updates, updated_at: new Date().toISOString() } : edu
    )
    onUpdate(updated)
  }, [education, onUpdate])

  const deleteEducation = useCallback((id: string) => {
    const updated = education.filter(edu => edu.id !== id)
    onUpdate(updated)
    if (editingId === id) {
      setEditingId(null)
    }
  }, [education, onUpdate, editingId])

  const addExtra = useCallback((educationId: string) => {
    const edu = education.find(e => e.id === educationId)
    if (!edu) return

    updateEducation(educationId, {
      extras: [...edu.extras, '']
    })
  }, [education, updateEducation])

  const updateExtra = useCallback((educationId: string, index: number, value: string) => {
    const edu = education.find(e => e.id === educationId)
    if (!edu) return

    const updatedExtras = [...edu.extras]
    updatedExtras[index] = value
    updateEducation(educationId, { extras: updatedExtras })
  }, [education, updateEducation])

  const deleteExtra = useCallback((educationId: string, index: number) => {
    const edu = education.find(e => e.id === educationId)
    if (!edu) return

    const updatedExtras = edu.extras.filter((_, i) => i !== index)
    updateEducation(educationId, { extras: updatedExtras })
  }, [education, updateEducation])

  return (
    <div className="space-y-4">
      {/* Add Education Button */}
      <button
        onClick={addEducation}
        className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
      >
        <div className="flex items-center justify-center space-x-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Add Education</span>
        </div>
      </button>

      {/* Education List */}
      {education.map((edu, index) => (
        <div key={edu.id} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">
              {edu.institution || 'New Institution'} - {edu.degree || 'New Degree'}
            </h4>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setEditingId(editingId === edu.id ? null : edu.id)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                {editingId === edu.id ? 'Done' : 'Edit'}
              </button>
              <button
                onClick={() => deleteEducation(edu.id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete
              </button>
            </div>
          </div>

          {editingId === edu.id && (
            <div className="space-y-4">
              {/* Institution and Degree */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Institution *
                  </label>
                  <input
                    type="text"
                    value={edu.institution}
                    onChange={(e) => updateEducation(edu.id, { institution: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="University Name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Degree *
                  </label>
                  <input
                    type="text"
                    value={edu.degree}
                    onChange={(e) => updateEducation(edu.id, { degree: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Bachelor of Science in Computer Science"
                  />
                </div>
              </div>

              {/* Location, Dates, and GPA */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={edu.location || ''}
                    onChange={(e) => updateEducation(edu.id, { location: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="City, State"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="text"
                    value={edu.start_date || ''}
                    onChange={(e) => updateEducation(edu.id, { start_date: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Sep 2016"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="text"
                    value={edu.end_date || ''}
                    onChange={(e) => updateEducation(edu.id, { end_date: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="May 2020"
                  />
                </div>
              </div>

              {/* GPA */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GPA
                </label>
                <input
                  type="text"
                  value={edu.gpa || ''}
                  onChange={(e) => updateEducation(edu.id, { gpa: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="3.8/4.0"
                />
              </div>

              {/* Additional Information */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Additional Information
                  </label>
                  <button
                    onClick={() => addExtra(edu.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add Item
                  </button>
                </div>
                
                <div className="space-y-2">
                  {edu.extras.map((extra, extraIndex) => (
                    <div key={extraIndex} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={extra}
                        onChange={(e) => updateExtra(edu.id, extraIndex, e.target.value)}
                        className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        placeholder="Honors, activities, relevant coursework..."
                      />
                      <button
                        onClick={() => deleteExtra(edu.id, extraIndex)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

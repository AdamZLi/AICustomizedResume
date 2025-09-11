'use client'

import { useState, useCallback } from 'react'
import { WorkExperience, BulletPoint } from '../types'

interface WorkExperienceEditorProps {
  workExperience: WorkExperience[]
  onUpdate: (workExperience: WorkExperience[]) => void
}

export default function WorkExperienceEditor({ workExperience, onUpdate }: WorkExperienceEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null)

  const addExperience = useCallback(() => {
    const newExperience: WorkExperience = {
      id: `exp_${Date.now()}`,
      company: '',
      title: '',
      location: '',
      start_date: '',
      end_date: '',
      is_current: false,
      bullets: [],
      order: workExperience.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    onUpdate([...workExperience, newExperience])
    setEditingId(newExperience.id)
  }, [workExperience, onUpdate])

  const updateExperience = useCallback((id: string, updates: Partial<WorkExperience>) => {
    const updated = workExperience.map(exp => 
      exp.id === id ? { ...exp, ...updates, updated_at: new Date().toISOString() } : exp
    )
    onUpdate(updated)
  }, [workExperience, onUpdate])

  const deleteExperience = useCallback((id: string) => {
    const updated = workExperience.filter(exp => exp.id !== id)
    onUpdate(updated)
    if (editingId === id) {
      setEditingId(null)
    }
  }, [workExperience, onUpdate, editingId])

  const addBullet = useCallback((experienceId: string) => {
    const experience = workExperience.find(exp => exp.id === experienceId)
    if (!experience) return

    const newBullet: BulletPoint = {
      id: `bullet_${Date.now()}`,
      text: '',
      is_active: true,
      order: experience.bullets.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    updateExperience(experienceId, {
      bullets: [...experience.bullets, newBullet]
    })
  }, [workExperience, updateExperience])

  const updateBullet = useCallback((experienceId: string, bulletId: string, updates: Partial<BulletPoint>) => {
    const experience = workExperience.find(exp => exp.id === experienceId)
    if (!experience) return

    const updatedBullets = experience.bullets.map(bullet =>
      bullet.id === bulletId ? { ...bullet, ...updates, updated_at: new Date().toISOString() } : bullet
    )

    updateExperience(experienceId, { bullets: updatedBullets })
  }, [workExperience, updateExperience])

  const deleteBullet = useCallback((experienceId: string, bulletId: string) => {
    const experience = workExperience.find(exp => exp.id === experienceId)
    if (!experience) return

    const updatedBullets = experience.bullets.filter(bullet => bullet.id !== bulletId)
    updateExperience(experienceId, { bullets: updatedBullets })
  }, [workExperience, updateExperience])

  return (
    <div className="space-y-4">
      {/* Add Experience Button */}
      <button
        onClick={addExperience}
        className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
      >
        <div className="flex items-center justify-center space-x-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Add Work Experience</span>
        </div>
      </button>

      {/* Experience List */}
      {workExperience.map((exp, index) => (
        <div key={exp.id} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">
              {exp.company || 'New Company'} - {exp.title || 'New Position'}
            </h4>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setEditingId(editingId === exp.id ? null : exp.id)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                {editingId === exp.id ? 'Done' : 'Edit'}
              </button>
              <button
                onClick={() => deleteExperience(exp.id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete
              </button>
            </div>
          </div>

          {editingId === exp.id && (
            <div className="space-y-4">
              {/* Company and Title */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company *
                  </label>
                  <input
                    type="text"
                    value={exp.company}
                    onChange={(e) => updateExperience(exp.id, { company: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Company Name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    value={exp.title}
                    onChange={(e) => updateExperience(exp.id, { title: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Job Title"
                  />
                </div>
              </div>

              {/* Location and Dates */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={exp.location || ''}
                    onChange={(e) => updateExperience(exp.id, { location: e.target.value })}
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
                    value={exp.start_date || ''}
                    onChange={(e) => updateExperience(exp.id, { start_date: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Jan 2020"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={exp.end_date || ''}
                      onChange={(e) => updateExperience(exp.id, { end_date: e.target.value })}
                      className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Present"
                      disabled={exp.is_current}
                    />
                    <label className="flex items-center text-sm text-gray-600">
                      <input
                        type="checkbox"
                        checked={exp.is_current}
                        onChange={(e) => updateExperience(exp.id, { 
                          is_current: e.target.checked,
                          end_date: e.target.checked ? 'Present' : ''
                        })}
                        className="mr-1"
                      />
                      Current
                    </label>
                  </div>
                </div>
              </div>

              {/* Bullet Points */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Achievements & Responsibilities
                  </label>
                  <button
                    onClick={() => addBullet(exp.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add Bullet
                  </button>
                </div>
                
                <div className="space-y-2">
                  {exp.bullets.map((bullet, bulletIndex) => (
                    <div key={bullet.id} className="flex items-start space-x-2">
                      <div className="flex items-center space-x-1 mt-2">
                        <input
                          type="checkbox"
                          checked={bullet.is_active}
                          onChange={(e) => updateBullet(exp.id, bullet.id, { is_active: e.target.checked })}
                          className="rounded"
                        />
                        <span className="text-gray-400 text-sm">•</span>
                      </div>
                      <div className="flex-1">
                        <textarea
                          value={bullet.text}
                          onChange={(e) => updateBullet(exp.id, bullet.id, { text: e.target.value })}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="Describe your achievement or responsibility..."
                          rows={2}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          {bullet.text.length}/220 characters
                        </p>
                      </div>
                      <button
                        onClick={() => deleteBullet(exp.id, bullet.id)}
                        className="text-red-600 hover:text-red-800 text-sm mt-2"
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

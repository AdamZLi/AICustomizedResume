'use client'

import { useState, useCallback } from 'react'
import { Entrepreneurship, BulletPoint } from '../types'

interface EntrepreneurshipEditorProps {
  entrepreneurship: Entrepreneurship[]
  onUpdate: (entrepreneurship: Entrepreneurship[]) => void
}

export default function EntrepreneurshipEditor({ entrepreneurship, onUpdate }: EntrepreneurshipEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null)

  const addVenture = useCallback(() => {
    const newVenture: Entrepreneurship = {
      id: `ent_${Date.now()}`,
      company: '',
      title: '',
      location: '',
      start_date: '',
      end_date: '',
      is_current: false,
      bullets: [],
      order: entrepreneurship.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    onUpdate([...entrepreneurship, newVenture])
    setEditingId(newVenture.id)
  }, [entrepreneurship, onUpdate])

  const updateVenture = useCallback((id: string, updates: Partial<Entrepreneurship>) => {
    const updated = entrepreneurship.map(ent => 
      ent.id === id ? { ...ent, ...updates, updated_at: new Date().toISOString() } : ent
    )
    onUpdate(updated)
  }, [entrepreneurship, onUpdate])

  const deleteVenture = useCallback((id: string) => {
    const updated = entrepreneurship.filter(ent => ent.id !== id)
    onUpdate(updated)
    if (editingId === id) {
      setEditingId(null)
    }
  }, [entrepreneurship, onUpdate, editingId])

  const addBullet = useCallback((ventureId: string) => {
    const venture = entrepreneurship.find(ent => ent.id === ventureId)
    if (!venture) return

    const newBullet: BulletPoint = {
      id: `bullet_${Date.now()}`,
      text: '',
      is_active: true,
      order: venture.bullets.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    updateVenture(ventureId, {
      bullets: [...venture.bullets, newBullet]
    })
  }, [entrepreneurship, updateVenture])

  const updateBullet = useCallback((ventureId: string, bulletId: string, updates: Partial<BulletPoint>) => {
    const venture = entrepreneurship.find(ent => ent.id === ventureId)
    if (!venture) return

    const updatedBullets = venture.bullets.map(bullet =>
      bullet.id === bulletId ? { ...bullet, ...updates, updated_at: new Date().toISOString() } : bullet
    )

    updateVenture(ventureId, { bullets: updatedBullets })
  }, [entrepreneurship, updateVenture])

  const deleteBullet = useCallback((ventureId: string, bulletId: string) => {
    const venture = entrepreneurship.find(ent => ent.id === ventureId)
    if (!venture) return

    const updatedBullets = venture.bullets.filter(bullet => bullet.id !== bulletId)
    updateVenture(ventureId, { bullets: updatedBullets })
  }, [entrepreneurship, updateVenture])

  return (
    <div className="space-y-4">
      {/* Add Venture Button */}
      <button
        onClick={addVenture}
        className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
      >
        <div className="flex items-center justify-center space-x-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Add Entrepreneurship Experience</span>
        </div>
      </button>

      {/* Venture List */}
      {entrepreneurship.map((ent, index) => (
        <div key={ent.id} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">
              {ent.company || 'New Venture'} - {ent.title || 'New Role'}
            </h4>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setEditingId(editingId === ent.id ? null : ent.id)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                {editingId === ent.id ? 'Done' : 'Edit'}
              </button>
              <button
                onClick={() => deleteVenture(ent.id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete
              </button>
            </div>
          </div>

          {editingId === ent.id && (
            <div className="space-y-4">
              {/* Company and Title */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company/Project *
                  </label>
                  <input
                    type="text"
                    value={ent.company}
                    onChange={(e) => updateVenture(ent.id, { company: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Company or Project Name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role/Title *
                  </label>
                  <input
                    type="text"
                    value={ent.title}
                    onChange={(e) => updateVenture(ent.id, { title: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Founder, CEO, etc."
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
                    value={ent.location || ''}
                    onChange={(e) => updateVenture(ent.id, { location: e.target.value })}
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
                    value={ent.start_date || ''}
                    onChange={(e) => updateVenture(ent.id, { start_date: e.target.value })}
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
                      value={ent.end_date || ''}
                      onChange={(e) => updateVenture(ent.id, { end_date: e.target.value })}
                      className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Present"
                      disabled={ent.is_current}
                    />
                    <label className="flex items-center text-sm text-gray-600">
                      <input
                        type="checkbox"
                        checked={ent.is_current}
                        onChange={(e) => updateVenture(ent.id, { 
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
                    Achievements & Impact
                  </label>
                  <button
                    onClick={() => addBullet(ent.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add Bullet
                  </button>
                </div>
                
                <div className="space-y-2">
                  {ent.bullets.map((bullet, bulletIndex) => (
                    <div key={bullet.id} className="flex items-start space-x-2">
                      <div className="flex items-center space-x-1 mt-2">
                        <input
                          type="checkbox"
                          checked={bullet.is_active}
                          onChange={(e) => updateBullet(ent.id, bullet.id, { is_active: e.target.checked })}
                          className="rounded"
                        />
                        <span className="text-gray-400 text-sm">•</span>
                      </div>
                      <div className="flex-1">
                        <textarea
                          value={bullet.text}
                          onChange={(e) => updateBullet(ent.id, bullet.id, { text: e.target.value })}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                          placeholder="Describe your achievement or impact..."
                          rows={2}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          {bullet.text.length}/220 characters
                        </p>
                      </div>
                      <button
                        onClick={() => deleteBullet(ent.id, bullet.id)}
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

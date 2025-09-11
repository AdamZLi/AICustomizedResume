'use client'

import { useState, useCallback } from 'react'
import { AdditionalInfo } from '../types'

interface AdditionalInfoEditorProps {
  additionalInfo: AdditionalInfo[]
  onUpdate: (additionalInfo: AdditionalInfo[]) => void
}

export default function AdditionalInfoEditor({ additionalInfo, onUpdate }: AdditionalInfoEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null)

  const addCategory = useCallback(() => {
    const newCategory: AdditionalInfo = {
      id: `info_${Date.now()}`,
      category: '',
      items: [],
      order: additionalInfo.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    onUpdate([...additionalInfo, newCategory])
    setEditingId(newCategory.id)
  }, [additionalInfo, onUpdate])

  const updateCategory = useCallback((id: string, updates: Partial<AdditionalInfo>) => {
    const updated = additionalInfo.map(info => 
      info.id === id ? { ...info, ...updates, updated_at: new Date().toISOString() } : info
    )
    onUpdate(updated)
  }, [additionalInfo, onUpdate])

  const deleteCategory = useCallback((id: string) => {
    const updated = additionalInfo.filter(info => info.id !== id)
    onUpdate(updated)
    if (editingId === id) {
      setEditingId(null)
    }
  }, [additionalInfo, onUpdate, editingId])

  const addItem = useCallback((categoryId: string) => {
    const category = additionalInfo.find(info => info.id === categoryId)
    if (!category) return

    updateCategory(categoryId, {
      items: [...category.items, '']
    })
  }, [additionalInfo, updateCategory])

  const updateItem = useCallback((categoryId: string, index: number, value: string) => {
    const category = additionalInfo.find(info => info.id === categoryId)
    if (!category) return

    const updatedItems = [...category.items]
    updatedItems[index] = value
    updateCategory(categoryId, { items: updatedItems })
  }, [additionalInfo, updateCategory])

  const deleteItem = useCallback((categoryId: string, index: number) => {
    const category = additionalInfo.find(info => info.id === categoryId)
    if (!category) return

    const updatedItems = category.items.filter((_, i) => i !== index)
    updateCategory(categoryId, { items: updatedItems })
  }, [additionalInfo, updateCategory])

  return (
    <div className="space-y-4">
      {/* Add Category Button */}
      <button
        onClick={addCategory}
        className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
      >
        <div className="flex items-center justify-center space-x-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Add Category</span>
        </div>
      </button>

      {/* Category List */}
      {additionalInfo.map((info, index) => (
        <div key={info.id} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">
              {info.category || 'New Category'} ({info.items.length} items)
            </h4>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setEditingId(editingId === info.id ? null : info.id)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                {editingId === info.id ? 'Done' : 'Edit'}
              </button>
              <button
                onClick={() => deleteCategory(info.id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete
              </button>
            </div>
          </div>

          {editingId === info.id && (
            <div className="space-y-4">
              {/* Category Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category Name *
                </label>
                <input
                  type="text"
                  value={info.category}
                  onChange={(e) => updateCategory(info.id, { category: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Skills, Certifications, Languages, etc."
                />
              </div>

              {/* Items */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Items
                  </label>
                  <button
                    onClick={() => addItem(info.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add Item
                  </button>
                </div>
                
                <div className="space-y-2">
                  {info.items.map((item, itemIndex) => (
                    <div key={itemIndex} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={item}
                        onChange={(e) => updateItem(info.id, itemIndex, e.target.value)}
                        className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        placeholder="Enter item..."
                      />
                      <button
                        onClick={() => deleteItem(info.id, itemIndex)}
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

          {/* Display items when not editing */}
          {editingId !== info.id && info.items.length > 0 && (
            <div className="mt-2">
              <div className="flex flex-wrap gap-2">
                {info.items.map((item, itemIndex) => (
                  <span
                    key={itemIndex}
                    className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

'use client'

import { useState } from 'react'
import { StructuredResume } from '../types'

interface LivePreviewProps {
  resume: StructuredResume
}

type PreviewMode = 'formatted' | 'raw'

export default function LivePreview({ resume }: LivePreviewProps) {
  const [previewMode, setPreviewMode] = useState<PreviewMode>('formatted')
  
  console.log("LivePreview received resume:", resume)

  const formatDateRange = (startDate?: string, endDate?: string, isCurrent?: boolean) => {
    if (!startDate) return ''
    
    if (isCurrent || endDate === 'Present' || endDate === 'Current') {
      return `${startDate} - Present`
    } else if (endDate) {
      return `${startDate} - ${endDate}`
    } else {
      return startDate
    }
  }

  const formatContactInfo = (contact: Record<string, string>) => {
    const parts = []
    if (contact.email) parts.push(contact.email)
    if (contact.phone) parts.push(contact.phone)
    if (contact.location) parts.push(contact.location)
    if (contact.linkedin) parts.push(contact.linkedin)
    return parts.join(' | ')
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Live Preview</h2>
            <p className="text-sm text-gray-600 mt-1">Real-time preview of your resume</p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPreviewMode('formatted')}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                previewMode === 'formatted'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Formatted
            </button>
            <button
              onClick={() => setPreviewMode('raw')}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                previewMode === 'raw'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Raw Text
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {previewMode === 'formatted' ? (
          <div className="p-6">
            <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
              {/* Header Section */}
              <div className="bg-gray-50 px-8 py-6 border-b border-gray-200">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {resume.headline.name}
                </h1>
                <h2 className="text-xl text-gray-700 mb-3">
                  {resume.headline.title}
                </h2>
                {resume.headline.summary && (
                  <p className="text-gray-600 leading-relaxed">
                    {resume.headline.summary}
                  </p>
                )}
                <div className="mt-4 text-sm text-gray-600">
                  {formatContactInfo(resume.headline.contact)}
                </div>
              </div>

              <div className="px-8 py-6 space-y-8">
                {/* Work Experience */}
                {resume.work_experience.length > 0 && (
                  <section>
                    <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-300">
                      PROFESSIONAL EXPERIENCE
                    </h3>
                    <div className="space-y-6">
                      {resume.work_experience.map((exp) => (
                        <div key={exp.id}>
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h4 className="font-semibold text-gray-900">
                                {exp.title}
                              </h4>
                              <p className="text-gray-700 font-medium">
                                {exp.company}
                                {exp.location && `, ${exp.location}`}
                              </p>
                            </div>
                            <div className="text-sm text-gray-600 text-right">
                              {formatDateRange(exp.start_date, exp.end_date, exp.is_current)}
                            </div>
                          </div>
                          {exp.bullets.filter(bullet => bullet.is_active).length > 0 && (
                            <ul className="list-disc list-inside space-y-1 ml-4">
                              {exp.bullets
                                .filter(bullet => bullet.is_active)
                                .map((bullet) => (
                                  <li key={bullet.id} className="text-gray-700 text-sm">
                                    {bullet.text}
                                  </li>
                                ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Entrepreneurship */}
                {resume.entrepreneurship.length > 0 && (
                  <section>
                    <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-300">
                      ENTREPRENEURSHIP
                    </h3>
                    <div className="space-y-6">
                      {resume.entrepreneurship.map((ent) => (
                        <div key={ent.id}>
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h4 className="font-semibold text-gray-900">
                                {ent.title}
                              </h4>
                              <p className="text-gray-700 font-medium">
                                {ent.company}
                                {ent.location && `, ${ent.location}`}
                              </p>
                            </div>
                            <div className="text-sm text-gray-600 text-right">
                              {formatDateRange(ent.start_date, ent.end_date, ent.is_current)}
                            </div>
                          </div>
                          {ent.bullets.filter(bullet => bullet.is_active).length > 0 && (
                            <ul className="list-disc list-inside space-y-1 ml-4">
                              {ent.bullets
                                .filter(bullet => bullet.is_active)
                                .map((bullet) => (
                                  <li key={bullet.id} className="text-gray-700 text-sm">
                                    {bullet.text}
                                  </li>
                                ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Education */}
                {resume.education.length > 0 && (
                  <section>
                    <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-300">
                      EDUCATION
                    </h3>
                    <div className="space-y-4">
                      {resume.education.map((edu) => (
                        <div key={edu.id}>
                          <div className="flex justify-between items-start mb-1">
                            <div>
                              <h4 className="font-semibold text-gray-900">
                                {edu.degree}
                              </h4>
                              <p className="text-gray-700 font-medium">
                                {edu.institution}
                                {edu.location && `, ${edu.location}`}
                              </p>
                            </div>
                            <div className="text-sm text-gray-600 text-right">
                              {formatDateRange(edu.start_date, edu.end_date)}
                            </div>
                          </div>
                          {edu.gpa && (
                            <p className="text-sm text-gray-600">GPA: {edu.gpa}</p>
                          )}
                          {edu.extras.length > 0 && (
                            <ul className="list-disc list-inside space-y-1 ml-4 mt-2">
                              {edu.extras.map((extra, index) => (
                                <li key={index} className="text-gray-700 text-sm">
                                  {extra}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Additional Information */}
                {resume.additional_info.length > 0 && (
                  <section>
                    <h3 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-300">
                      ADDITIONAL INFORMATION
                    </h3>
                    <div className="space-y-4">
                      {resume.additional_info.map((info) => (
                        <div key={info.id}>
                          <h4 className="font-semibold text-gray-900 mb-2">
                            {info.category}
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {info.items.map((item, index) => (
                              <span
                                key={index}
                                className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm"
                              >
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Raw Text Output</h3>
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                {generateRawText(resume)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function generateRawText(resume: StructuredResume): string {
  let text = ''
  
  // Header
  text += `${resume.headline.name}\n`
  text += `${resume.headline.title}\n`
  if (resume.headline.summary) {
    text += `${resume.headline.summary}\n`
  }
  
  const contactParts = []
  if (resume.headline.contact.email) contactParts.push(resume.headline.contact.email)
  if (resume.headline.contact.phone) contactParts.push(resume.headline.contact.phone)
  if (resume.headline.contact.location) contactParts.push(resume.headline.contact.location)
  if (resume.headline.contact.linkedin) contactParts.push(resume.headline.contact.linkedin)
  if (contactParts.length > 0) {
    text += `${contactParts.join(' | ')}\n`
  }
  
  text += '\n'
  
  // Work Experience
  if (resume.work_experience.length > 0) {
    text += 'PROFESSIONAL EXPERIENCE\n'
    text += '=====================\n\n'
    
    resume.work_experience.forEach(exp => {
      text += `${exp.title}\n`
      text += `${exp.company}`
      if (exp.location) text += `, ${exp.location}`
      text += '\n'
      
      if (exp.start_date) {
        const endDate = exp.is_current ? 'Present' : exp.end_date
        text += `${exp.start_date} - ${endDate}\n`
      }
      
      exp.bullets.filter(bullet => bullet.is_active).forEach(bullet => {
        text += `• ${bullet.text}\n`
      })
      text += '\n'
    })
  }
  
  // Entrepreneurship
  if (resume.entrepreneurship.length > 0) {
    text += 'ENTREPRENEURSHIP\n'
    text += '================\n\n'
    
    resume.entrepreneurship.forEach(ent => {
      text += `${ent.title}\n`
      text += `${ent.company}`
      if (ent.location) text += `, ${ent.location}`
      text += '\n'
      
      if (ent.start_date) {
        const endDate = ent.is_current ? 'Present' : ent.end_date
        text += `${ent.start_date} - ${endDate}\n`
      }
      
      ent.bullets.filter(bullet => bullet.is_active).forEach(bullet => {
        text += `• ${bullet.text}\n`
      })
      text += '\n'
    })
  }
  
  // Education
  if (resume.education.length > 0) {
    text += 'EDUCATION\n'
    text += '=========\n\n'
    
    resume.education.forEach(edu => {
      text += `${edu.degree}\n`
      text += `${edu.institution}`
      if (edu.location) text += `, ${edu.location}`
      text += '\n'
      
      if (edu.start_date) {
        text += `${edu.start_date} - ${edu.end_date || 'Present'}\n`
      }
      
      if (edu.gpa) {
        text += `GPA: ${edu.gpa}\n`
      }
      
      edu.extras.forEach(extra => {
        text += `• ${extra}\n`
      })
      text += '\n'
    })
  }
  
  // Additional Information
  if (resume.additional_info.length > 0) {
    text += 'ADDITIONAL INFORMATION\n'
    text += '=====================\n\n'
    
    resume.additional_info.forEach(info => {
      text += `${info.category}\n`
      text += `${info.items.join(', ')}\n\n`
    })
  }
  
  return text.trim()
}

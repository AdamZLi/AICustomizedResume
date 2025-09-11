'use client'

import { useState, useCallback } from 'react'
import { StructuredResume, SectionType, WorkExperience, Entrepreneurship, Education, AdditionalInfo, Headline, BulletPoint } from '../types'
import HeadlineEditor from './HeadlineEditor'
import WorkExperienceEditor from './WorkExperienceEditor'
import EntrepreneurshipEditor from './EntrepreneurshipEditor'
import EducationEditor from './EducationEditor'
import AdditionalInfoEditor from './AdditionalInfoEditor'

interface StructuredEditorProps {
  resume: StructuredResume
  onResumeUpdate: (resume: StructuredResume) => void
}

export default function StructuredEditor({ resume, onResumeUpdate }: StructuredEditorProps) {
  const [activeSection, setActiveSection] = useState<SectionType>(SectionType.HEADLINE)
  const [expandedSections, setExpandedSections] = useState<Set<SectionType>>(new Set([SectionType.HEADLINE]))
  
  console.log("StructuredEditor received resume:", resume)

  const handleSectionToggle = (section: SectionType) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(section)) {
        newSet.delete(section)
      } else {
        newSet.add(section)
      }
      return newSet
    })
  }

  const handleHeadlineUpdate = useCallback((headline: Headline) => {
    const updatedResume = { ...resume, headline }
    onResumeUpdate(updatedResume)
  }, [resume, onResumeUpdate])

  const handleWorkExperienceUpdate = useCallback((workExperience: WorkExperience[]) => {
    const updatedResume = { ...resume, work_experience: workExperience }
    onResumeUpdate(updatedResume)
  }, [resume, onResumeUpdate])

  const handleEntrepreneurshipUpdate = useCallback((entrepreneurship: Entrepreneurship[]) => {
    const updatedResume = { ...resume, entrepreneurship }
    onResumeUpdate(updatedResume)
  }, [resume, onResumeUpdate])

  const handleEducationUpdate = useCallback((education: Education[]) => {
    const updatedResume = { ...resume, education }
    onResumeUpdate(updatedResume)
  }, [resume, onResumeUpdate])

  const handleAdditionalInfoUpdate = useCallback((additionalInfo: AdditionalInfo[]) => {
    const updatedResume = { ...resume, additional_info: additionalInfo }
    onResumeUpdate(updatedResume)
  }, [resume, onResumeUpdate])

  const sections = [
    {
      type: SectionType.HEADLINE,
      title: 'Headline',
      count: 1,
      icon: '👤'
    },
    {
      type: SectionType.WORK_EXPERIENCE,
      title: 'Work Experience',
      count: resume.work_experience.length,
      icon: '💼'
    },
    {
      type: SectionType.ENTREPRENEURSHIP,
      title: 'Entrepreneurship',
      count: resume.entrepreneurship.length,
      icon: '🚀'
    },
    {
      type: SectionType.EDUCATION,
      title: 'Education',
      count: resume.education.length,
      icon: '🎓'
    },
    {
      type: SectionType.ADDITIONAL_INFO,
      title: 'Additional Info',
      count: resume.additional_info.length,
      icon: '📋'
    }
  ]

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Resume Editor</h2>
        <p className="text-sm text-gray-600 mt-1">Edit your resume sections below</p>
      </div>

      {/* Section Navigation */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex flex-wrap gap-2">
          {sections.map((section) => (
            <button
              key={section.type}
              onClick={() => {
                setActiveSection(section.type)
                handleSectionToggle(section.type)
              }}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeSection === section.type
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <span>{section.icon}</span>
              <span>{section.title}</span>
              <span className="bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                {section.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Headline Section */}
          <div className="border border-gray-200 rounded-lg">
            <button
              onClick={() => handleSectionToggle(SectionType.HEADLINE)}
              className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">👤</span>
                <div>
                  <h3 className="font-medium text-gray-900">Headline</h3>
                  <p className="text-sm text-gray-600">Name, title, and contact information</p>
                </div>
              </div>
              <svg
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  expandedSections.has(SectionType.HEADLINE) ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has(SectionType.HEADLINE) && (
              <div className="border-t border-gray-200 p-4">
                <HeadlineEditor
                  headline={resume.headline}
                  onUpdate={handleHeadlineUpdate}
                />
              </div>
            )}
          </div>

          {/* Work Experience Section */}
          <div className="border border-gray-200 rounded-lg">
            <button
              onClick={() => handleSectionToggle(SectionType.WORK_EXPERIENCE)}
              className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">💼</span>
                <div>
                  <h3 className="font-medium text-gray-900">Work Experience</h3>
                  <p className="text-sm text-gray-600">{resume.work_experience.length} positions</p>
                </div>
              </div>
              <svg
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  expandedSections.has(SectionType.WORK_EXPERIENCE) ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has(SectionType.WORK_EXPERIENCE) && (
              <div className="border-t border-gray-200 p-4">
                <WorkExperienceEditor
                  workExperience={resume.work_experience}
                  onUpdate={handleWorkExperienceUpdate}
                />
              </div>
            )}
          </div>

          {/* Entrepreneurship Section */}
          <div className="border border-gray-200 rounded-lg">
            <button
              onClick={() => handleSectionToggle(SectionType.ENTREPRENEURSHIP)}
              className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">🚀</span>
                <div>
                  <h3 className="font-medium text-gray-900">Entrepreneurship</h3>
                  <p className="text-sm text-gray-600">{resume.entrepreneurship.length} ventures</p>
                </div>
              </div>
              <svg
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  expandedSections.has(SectionType.ENTREPRENEURSHIP) ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has(SectionType.ENTREPRENEURSHIP) && (
              <div className="border-t border-gray-200 p-4">
                <EntrepreneurshipEditor
                  entrepreneurship={resume.entrepreneurship}
                  onUpdate={handleEntrepreneurshipUpdate}
                />
              </div>
            )}
          </div>

          {/* Education Section */}
          <div className="border border-gray-200 rounded-lg">
            <button
              onClick={() => handleSectionToggle(SectionType.EDUCATION)}
              className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">🎓</span>
                <div>
                  <h3 className="font-medium text-gray-900">Education</h3>
                  <p className="text-sm text-gray-600">{resume.education.length} institutions</p>
                </div>
              </div>
              <svg
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  expandedSections.has(SectionType.EDUCATION) ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has(SectionType.EDUCATION) && (
              <div className="border-t border-gray-200 p-4">
                <EducationEditor
                  education={resume.education}
                  onUpdate={handleEducationUpdate}
                />
              </div>
            )}
          </div>

          {/* Additional Info Section */}
          <div className="border border-gray-200 rounded-lg">
            <button
              onClick={() => handleSectionToggle(SectionType.ADDITIONAL_INFO)}
              className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">📋</span>
                <div>
                  <h3 className="font-medium text-gray-900">Additional Info</h3>
                  <p className="text-sm text-gray-600">{resume.additional_info.length} categories</p>
                </div>
              </div>
              <svg
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  expandedSections.has(SectionType.ADDITIONAL_INFO) ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has(SectionType.ADDITIONAL_INFO) && (
              <div className="border-t border-gray-200 p-4">
                <AdditionalInfoEditor
                  additionalInfo={resume.additional_info}
                  onUpdate={handleAdditionalInfoUpdate}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

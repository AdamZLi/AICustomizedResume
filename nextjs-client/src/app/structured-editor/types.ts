// TypeScript types for structured resume editing

export enum SectionType {
  HEADLINE = "headline",
  WORK_EXPERIENCE = "work_experience",
  ENTREPRENEURSHIP = "entrepreneurship",
  EDUCATION = "education",
  ADDITIONAL_INFO = "additional_info",
  SKILLS = "skills"
}

export interface BulletPoint {
  id: string
  text: string
  is_active: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface WorkExperience {
  id: string
  company: string
  title: string
  location?: string
  start_date?: string
  end_date?: string
  is_current: boolean
  bullets: BulletPoint[]
  order: number
  created_at: string
  updated_at: string
}

export interface Entrepreneurship {
  id: string
  company: string
  title: string
  location?: string
  start_date?: string
  end_date?: string
  is_current: boolean
  bullets: BulletPoint[]
  order: number
  created_at: string
  updated_at: string
}

export interface Education {
  id: string
  institution: string
  degree: string
  location?: string
  start_date?: string
  end_date?: string
  gpa?: string
  extras: string[]
  order: number
  created_at: string
  updated_at: string
}

export interface Headline {
  name: string
  title: string
  summary?: string
  contact: Record<string, string>
  created_at: string
  updated_at: string
}

export interface AdditionalInfo {
  id: string
  category: string
  items: string[]
  order: number
  created_at: string
  updated_at: string
}

export interface StructuredResume {
  id: string
  original_filename: string
  headline: Headline
  work_experience: WorkExperience[]
  entrepreneurship: Entrepreneurship[]
  education: Education[]
  additional_info: AdditionalInfo[]
  created_at: string
  updated_at: string
}

// API Request/Response types
export interface StructuredResumeResponse {
  resume: StructuredResume
}

export interface SectionUpdateRequest {
  resume_id: string
  section_type: SectionType
  section_data: WorkExperience | Entrepreneurship | Education | AdditionalInfo | Headline
}

export interface BulletPointUpdateRequest {
  resume_id: string
  section_type: SectionType
  section_id: string
  bullet: BulletPoint
}

export interface ResumeExportRequest {
  resume_id: string
  format: string
  include_annotations: boolean
}

export interface KeywordInsertionRequest {
  resume_id: string
  keywords: string[]
  max_insertions_per_bullet: number
  max_chars_per_insertion: number
}

export interface KeywordInsertionSuggestion {
  bullet_id: string
  insertion_text: string
  insertion_type: string
  keywords_used: string[]
  confidence: number
}

export interface KeywordInsertionResponse {
  suggestions: KeywordInsertionSuggestion[]
  skipped_keywords: string[]
}

export interface ResumeParseRequest {
  resume_id: string
  parse_options: Record<string, any>
}

export interface ResumeParseResponse {
  resume_id: string
  structured_resume: StructuredResume
  parse_summary: Record<string, any>
  warnings: string[]
}

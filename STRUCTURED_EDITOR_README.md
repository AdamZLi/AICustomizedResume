# Structured Resume Editor

A comprehensive structured resume editing system that allows users to upload PDF/DOCX resumes, parse them into editable sections, and make targeted edits with live preview and keyword insertion capabilities.

## Features

### 1. Upload & Pre-fill
- **Supported Formats**: PDF (≤10MB), DOCX (≤10MB)
- **Storage**: Temporary object store with original file + parsed JSON
- **Auto-parsing**: Automatically parses uploaded resumes into structured format

### 2. Enhanced Parsing Engine
- **Section Detection**: Automatically identifies resume sections using regex patterns
  - Work Experience
  - Entrepreneurship
  - Education
  - Additional Information
  - Skills
- **Bullet Point Extraction**: Recognizes various bullet formats (•, -, –, numbered lists)
- **Date Parsing**: Extracts start/end dates with support for "Present" indicators
- **Contact Information**: Automatically extracts name, title, email, phone, location, LinkedIn
- **Fallback Handling**: Unmatched content goes to "Additional Info" section

### 3. Structured Editor (Left Panel)
- **Section-based Editing**: Organized by resume sections with collapsible interface
- **Inline Editing**: Direct text editing with real-time validation
- **Drag & Drop**: Reorderable sections and bullet points
- **Character Limits**: Built-in validation (80-220 chars for bullets)
- **Add/Delete Controls**: Easy section and bullet point management

### 4. Live Preview (Right Panel)
- **Real-time Updates**: Instant preview of changes
- **ATS-safe Template**: Clean, single-column layout optimized for ATS systems
- **Multiple Views**: Formatted preview and raw text output
- **Professional Styling**: Clean, modern resume formatting

### 5. Autosave & Export
- **Debounced Autosave**: 800ms delay to prevent excessive API calls
- **Visual Indicators**: Save status with loading states
- **Export Options**: PDF and HTML formats
- **Change Tracking**: Visual indicators for unsaved changes

### 6. Keyword Insertion System
- **Micro-edits**: Proposes tiny, line-level keyword insertions
- **Smart Suggestions**: AI-powered insertion recommendations
- **Per-bullet Control**: Accept/reject individual suggestions
- **Character Limits**: Enforces caps (2 words / 25 chars per insertion)
- **Confidence Scoring**: Shows confidence levels for each suggestion

## Architecture

### Backend Components

#### Data Models (`models_structured.py`)
```python
- StructuredResume: Main resume container
- Headline: Name, title, contact info
- WorkExperience: Company, role, dates, bullets
- Entrepreneurship: Startup experience
- Education: Institution, degree, dates, extras
- AdditionalInfo: Skills, certifications, etc.
- BulletPoint: Individual achievements with metadata
```

#### Parser Service (`services/structured_parser.py`)
```python
- Section detection with regex patterns
- Bullet point extraction
- Date parsing and normalization
- Contact information extraction
- Fallback handling for unmatched content
```

#### Storage Service (`services/structured_storage.py`)
```python
- JSON-based storage for structured data
- Metadata tracking
- CRUD operations
- File management
```

#### API Router (`routers/structured_resume.py`)
```python
- Parse resume endpoint
- CRUD operations for sections
- Bullet point management
- Export functionality
- Keyword insertion suggestions
```

### Frontend Components

#### Main Page (`structured-editor/page.tsx`)
- Resume loading and error handling
- Autosave integration
- Export functionality
- Navigation and header

#### Structured Editor (`components/StructuredEditor.tsx`)
- Section navigation
- Collapsible sections
- Section-specific editors

#### Section Editors
- `HeadlineEditor.tsx`: Name, title, contact info
- `WorkExperienceEditor.tsx`: Jobs with bullets
- `EntrepreneurshipEditor.tsx`: Startup experience
- `EducationEditor.tsx`: Academic background
- `AdditionalInfoEditor.tsx`: Skills and extras

#### Live Preview (`components/LivePreview.tsx`)
- Real-time formatted preview
- Raw text output
- ATS-safe styling

#### Keyword Insertion (`components/KeywordInsertion.tsx`)
- Suggestion display
- Apply/dismiss controls
- Confidence indicators

#### Autosave Hook (`hooks/useAutosave.ts`)
- Debounced saving
- Error handling
- Loading states

## API Endpoints

### Resume Parsing
```
POST /structured-resume/parse
{
  "resume_id": "string",
  "parse_options": {}
}
```

### Get Structured Resume
```
GET /structured-resume/{resume_id}
```

### Update Section
```
PUT /structured-resume/{resume_id}/section
{
  "resume_id": "string",
  "section_type": "headline|work_experience|entrepreneurship|education|additional_info",
  "section_data": {...}
}
```

### Update Bullet Point
```
PUT /structured-resume/{resume_id}/bullet
{
  "resume_id": "string",
  "section_type": "string",
  "section_id": "string",
  "bullet": {...}
}
```

### Export Resume
```
POST /structured-resume/{resume_id}/export
{
  "resume_id": "string",
  "format": "pdf|html",
  "include_annotations": false
}
```

### Keyword Insertions
```
POST /structured-resume/{resume_id}/keyword-insertions
{
  "resume_id": "string",
  "keywords": ["string"],
  "max_insertions_per_bullet": 2,
  "max_chars_per_insertion": 25
}
```

## Usage Flow

1. **Upload Resume**: User uploads PDF/DOCX file
2. **Auto-parse**: System automatically parses into structured format
3. **Edit**: User opens structured editor to make changes
4. **Live Preview**: Changes appear instantly in right panel
5. **Autosave**: Changes are automatically saved with debouncing
6. **Keyword Insertion**: Optional AI-powered keyword suggestions
7. **Export**: Generate final PDF/HTML resume

## Integration with Existing System

The structured editor integrates seamlessly with the existing keyword-based resume tailoring system:

- **Upload Integration**: Main page automatically parses uploaded resumes
- **Editor Access**: "Edit Resume" button opens structured editor
- **Keyword System**: Can be used alongside existing keyword extraction
- **Export Compatibility**: Exports work with existing PDF generation

## Future Enhancements

- **Drag & Drop Reordering**: Full drag-and-drop for sections and bullets
- **Template System**: Multiple resume templates
- **Collaboration**: Multi-user editing capabilities
- **Version History**: Track changes over time
- **Advanced Parsing**: Better handling of complex resume formats
- **AI Suggestions**: More sophisticated content suggestions

## Technical Notes

- **Performance**: Debounced autosave prevents API spam
- **Error Handling**: Comprehensive error states and recovery
- **Responsive Design**: Works on desktop and mobile
- **Accessibility**: Keyboard navigation and screen reader support
- **Type Safety**: Full TypeScript coverage for frontend
- **Validation**: Input validation on both frontend and backend

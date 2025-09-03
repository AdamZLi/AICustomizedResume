# Plan-and-Annotate Resume Tailoring Workflow

This document describes the new plan-and-annotate workflow that replaces the previous rewrite approach. The new workflow preserves the original PDF structure while adding minimal, targeted insertions to incorporate keywords.

## Overview

The plan-and-annotate workflow consists of three main phases:

1. **Edit Plan Generation** - AI analyzes the resume and proposes minimal insertions
2. **Plan Application** - Edits are safely applied with validation
3. **PDF Annotation** - Original PDF is annotated with highlights and notes

## Key Benefits

- ✅ **Preserves Original Layout** - No restructuring or reordering of content
- ✅ **Minimal Changes** - Maximum 2 words or 25 characters per line
- ✅ **Safe Edits** - Validation ensures changes don't break formatting
- ✅ **Visual Feedback** - Annotated PDF shows exactly what changed
- ✅ **Audit Trail** - Complete change log for transparency

## Architecture

### Services

#### 1. EditPlanService (`services/edit_plan.py`)
- Generates structured edit plans using OpenAI's structured outputs
- Proposes minimal insertions using three strategies:
  - **Modifier**: Add word before existing content
  - **Parenthetical**: Add brief parenthetical addition
  - **Tail**: Add tiny tail addition after existing content
- Returns JSON schema-compliant edit plans

#### 2. ApplyPlanService (`services/apply_plan.py`)
- Safely applies edit plans with comprehensive validation
- Enforces constraints:
  - Character delta ≤ 25
  - Word delta ≤ 2
  - Levenshtein distance ≤ 25
  - Original structure preservation
- Generates change logs and diff previews

#### 3. PDFAnnotator (`services/pdf_annotate.py`)
- Adds highlights and sticky notes to original PDF
- Uses PyMuPDF for precise annotation
- Fallback notes for text that can't be located
- Returns annotated PDF without changing original content

#### 4. ResumeSectionService (`services/sections.py`)
- Identifies best sections for keyword incorporation
- Calculates keyword relevance scores
- Provides section-based text processing

### API Endpoints

#### Generate Edit Plan
```http
POST /resume/edit-plan
Content-Type: application/json

{
  "resume_id": "uuid",
  "selected_keywords": ["Python", "Docker", "Kubernetes"],
  "job_title": "Software Engineer"
}
```

#### Apply Edit Plan
```http
POST /resume/apply-plan
Content-Type: application/json

{
  "resume_id": "uuid",
  "edit_plan": {...},
  "section_name": "experience"
}
```

#### Create Annotated PDF
```http
POST /resume/{resume_id}/annotate
Content-Type: multipart/form-data

edit_plan: {...}
section_name: "experience"
```

#### Download Annotated PDF
```http
GET /resume/{resume_id}/annotated.pdf
```

## Edit Strategies

### 1. Modifier Strategy
- **Purpose**: Add descriptive words before existing content
- **Example**: "experienced" → "experienced Python developer"
- **Use Case**: Adding skill levels or technology expertise

### 2. Parenthetical Strategy
- **Purpose**: Add brief clarifications or additional context
- **Example**: "Python" → "Python (with Django)"
- **Use Case**: Specifying frameworks or tools

### 3. Tail Strategy
- **Purpose**: Add small additions at the end of lines
- **Example**: "testing" → "testing, using A/B testing"
- **Use Case**: Adding methodologies or specific techniques

## Validation Rules

### Character Constraints
- Maximum insertion: 25 characters
- Maximum change per line: 25 characters
- Levenshtein distance: ≤ 25

### Word Constraints
- Maximum words added: 2 per line
- Original structure preservation: ≥ 70% word overlap

### Content Preservation
- No reordering of lines or bullets
- No deletion of existing content
- Maintains original meaning and flow

## Workflow Example

### Step 1: Generate Edit Plan
```python
# AI analyzes resume and generates plan
edit_plan = {
    "edits": [
        {
            "line": 1,
            "strategy": "tail",
            "after_anchor": "Node.js",
            "insertion": ", using Python",
            "keywords_used": ["Python"]
        },
        {
            "line": 3,
            "strategy": "parenthetical",
            "after_anchor": "Agile",
            "insertion": "(with Docker)",
            "keywords_used": ["Docker"]
        }
    ],
    "skipped_keywords": ["machine learning", "data analysis"]
}
```

### Step 2: Apply Edits
```python
# Edits are applied with validation
updated_lines, change_log, applied_keywords = apply_plan_service.apply_edit_plan(
    original_lines=original_lines,
    edit_plan=edit_plan
)
```

### Step 3: Annotate PDF
```python
# Original PDF is annotated with highlights and notes
annotated_path = pdf_annotator.annotate_pdf_with_edits(
    pdf_path=original_pdf_path,
    edit_plan=edit_plan,
    original_lines=original_lines
)
```

## Error Handling

### Edit Plan Generation
- Falls back to empty plan if OpenAI API fails
- Logs errors for debugging
- Returns all keywords as skipped on failure

### Plan Application
- Validates each edit individually
- Skips invalid edits with warning logs
- Continues processing remaining edits
- Returns partial results on errors

### PDF Annotation
- Falls back to original PDF on annotation failure
- Adds fallback notes when text location is unclear
- Logs warnings for debugging

## Testing

Run the test suite to verify functionality:

```bash
python3 test_edit_plan_workflow.py
```

The test suite covers:
- Edit plan generation (mock)
- Plan application with validation
- Diff preview generation
- PDF annotation (mock)
- Validation logic testing

## Dependencies

### Required Packages
- `openai>=1.0.0` - OpenAI API client
- `PyMuPDF>=1.23.0` - PDF annotation
- `python-Levenshtein>=0.21.0` - Edit validation
- `fastapi>=0.104.1` - Web framework
- `pydantic>=2.5.0` - Data validation

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Migration from Rewrite Workflow

### What Changed
- **Before**: Complete resume rewriting with new PDF generation
- **After**: Minimal edits with original PDF annotation

### Benefits of New Approach
- Faster processing (no full rewrite)
- Better preservation of original formatting
- Clearer audit trail of changes
- More predictable results

### API Compatibility
- New endpoints are additive
- Old rewrite endpoint still available
- Gradual migration path supported

## Future Enhancements

### Planned Features
- Batch processing for multiple resumes
- Custom annotation styles and colors
- Export to different annotation formats
- Integration with ATS systems

### Performance Optimizations
- Caching of edit plans
- Parallel processing of sections
- Optimized PDF search algorithms

## Troubleshooting

### Common Issues

#### Edit Plan Generation Fails
- Check OpenAI API key configuration
- Verify API quota and rate limits
- Check network connectivity

#### Edits Not Applied
- Review validation error logs
- Check character/word constraints
- Verify original text structure

#### PDF Annotation Issues
- Ensure PyMuPDF is properly installed
- Check PDF file permissions
- Verify text search accuracy

### Debug Mode
Enable detailed logging by setting log level to DEBUG in your environment.

## Support

For issues or questions about the plan-and-annotate workflow:
1. Check the logs for error details
2. Run the test suite to verify functionality
3. Review the validation constraints
4. Check API endpoint documentation


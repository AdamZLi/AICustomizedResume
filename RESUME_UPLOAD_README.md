# Resume Upload & Preview - Slice #2

This document describes the implementation of Slice #2: PDF upload and preview functionality.

## What's Been Implemented

### Backend (FastAPI)

#### New Dependencies
- `pypdf>=3.17.0` - For PDF text extraction

#### New Services
- **`services/storage.py`** - Handles PDF file storage and retrieval
- **`services/resume_parser.py`** - Extracts text from PDF files

#### New Models
- **`ResumeUploadResponse`** - Response model for upload endpoint
- **`ResumeTextResponse`** - Response model for text extraction

#### New Endpoints
- **`POST /resume/upload`** - Upload PDF resume
- **`GET /resume/{resume_id}/pdf`** - View PDF inline
- **`GET /resume/{resume_id}/text`** - Get extracted text

#### Features
- PDF validation (MIME type, file size < 10MB)
- Unique resume ID generation (UUID)
- Local disk storage in `uploads/` directory
- Text extraction with 800-character preview
- Inline PDF viewing with proper headers

### Frontend (Next.js)

#### New API Routes
- **`/api/upload_resume`** - Proxies to FastAPI upload endpoint
- **`/api/resume/[id]/pdf`** - Proxies to FastAPI PDF endpoint
- **`/api/resume/[id]/text`** - Proxies to FastAPI text endpoint

#### UI Components
- PDF file selection with validation
- Upload button with loading states
- Success confirmation with file details
- Inline PDF preview using iframe
- Text excerpt display (first 800 characters)
- Error handling and user feedback

## Project Structure

```
├── services/
│   ├── __init__.py
│   ├── storage.py          # PDF file operations
│   └── resume_parser.py    # Text extraction
├── routers/
│   ├── __init__.py
│   └── resume.py           # Resume API endpoints
├── models.py               # Updated with new models
├── main.py                 # Updated with resume router
├── nextjs-client/src/app/
│   ├── api/
│   │   ├── upload_resume/route.ts
│   │   └── resume/[id]/
│   │       ├── pdf/route.ts
│   │       └── text/route.ts
│   └── page.tsx            # Updated with upload UI
└── requirements.txt        # Updated with pypdf
```

## How to Use

### 1. Start the Backend
```bash
python3 main.py
```

### 2. Start the Frontend
```bash
cd nextjs-client
npm run dev
```

### 3. Upload a Resume
1. Navigate to the app
2. Select a PDF file (max 10MB)
3. Click "Upload & Preview"
4. View the PDF inline and text excerpt

### 4. Test the API
```bash
python3 test_resume_api.py
```

## Security & Validation

- Only PDF files accepted (MIME type validation)
- File size limit: 10MB
- Unique filename generation (UUID-based)
- Input sanitization and error handling
- Proper HTTP status codes and error messages

## Next Steps (Future Slices)

- Resume tailoring with extracted keywords
- Keyword matching and highlighting
- Resume versioning and comparison
- Cloud storage integration (S3, etc.)

## Testing

The implementation includes:
- Comprehensive error handling
- File validation
- Text extraction testing
- PDF streaming verification
- Frontend state management
- Loading and error states

## Constraints Met

✅ **Vertical slice** - Complete UI → API → model → output flow  
✅ **Minimal dependencies** - Only added pypdf  
✅ **File size limits** - 10MB max  
✅ **Clean architecture** - Services separated, <300 lines per file  
✅ **Error handling** - Comprehensive validation and user feedback  
✅ **Persistence** - Local disk storage for dev environment  
✅ **Inline preview** - PDF viewable in browser  
✅ **Text extraction** - First 800 characters for preview  
✅ **Stable IDs** - UUID-based resume identification  
✅ **No CORS issues** - Next.js proxy pattern  
✅ **Existing code untouched** - Only added new functionality

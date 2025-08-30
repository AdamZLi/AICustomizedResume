# Resume Tailoring API

A FastAPI-based web application that extracts keywords from job descriptions using OpenAI's GPT model. This is the first vertical slice of a larger resume tailoring system.

## Features

- **Keyword Extraction**: Extract relevant keywords, skills, and tools from job descriptions
- **OpenAI Integration**: Uses GPT-3.5-turbo for intelligent keyword analysis
- **Input Validation**: Comprehensive error handling and input validation
- **RESTful API**: Clean, documented API endpoints
- **Auto-generated Docs**: Interactive API documentation at `/docs`

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd Attempt2
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=your_actual_api_key_here
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Endpoints

### POST /keywords_text

Extract keywords, skills, and tools from job description text.

**Request Body:**
```json
{
  "job_text": "Your job description here...",
  "max_terms": 30
}
```

**Response:**
```json
{
  "keywords": ["term1", "term2", "term3"],
  "skills": ["skill1", "skill2", "skill3"],
  "tools": ["tool1", "tool2", "tool3"]
}
```

**Parameters:**
- `job_text` (required): The job description text to analyze
- `max_terms` (optional): Maximum number of terms to extract (default: 30, max: 100)

### GET /health

Health check endpoint to verify service status.

### GET /

Root endpoint with basic API information.

## Testing

Run the test suite to verify the API functionality:

```bash
python test_api.py
```

The test script includes:
- Health check verification
- Sample job descriptions testing
- Error handling validation
- Multiple job types (Software Engineer, Data Scientist, Product Manager)

## Example Usage

### cURL Example

```bash
curl -X POST "http://localhost:8000/keywords_text" \
     -H "Content-Type: application/json" \
     -d '{
       "job_text": "We need a Python developer with experience in Django, React, and AWS.",
       "max_terms": 15
     }'
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8000/keywords_text",
    json={
        "job_text": "We need a Python developer with experience in Django, React, and AWS.",
        "max_terms": 15
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Keywords: {result['keywords']}")
    print(f"Skills: {result['skills']}")
    print(f"Tools: {result['tools']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Architecture

This implementation follows the vertical slice architecture:

- **UI Layer**: FastAPI with auto-generated documentation
- **API Layer**: RESTful endpoints with Pydantic validation
- **Model Layer**: OpenAI GPT-3.5-turbo integration
- **Output**: Structured JSON response with extracted keywords

## Error Handling

The API includes comprehensive error handling for:
- Empty or invalid job text
- OpenAI API failures
- JSON parsing errors
- Invalid input parameters
- Network connectivity issues

## Development

### Project Structure

```
Attempt2/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── env.example         # Environment variables template
├── test_api.py         # Test suite
└── README.md           # This file
```

### Adding New Features

To extend this vertical slice:
1. Add new Pydantic models in `main.py`
2. Create new endpoints following the existing pattern
3. Update the test suite in `test_api.py`
4. Document changes in `README.md`

## Next Steps

This is the first vertical slice. Future slices will include:
- Resume upload and parsing
- Keyword matching and scoring
- Resume tailoring suggestions
- Change tracking and visualization

## Troubleshooting

### Common Issues

1. **OpenAI API Error**: Check your API key in `.env` file
2. **Port Already in Use**: Change the port in `main.py` or kill existing processes
3. **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

### Logs

The application logs errors and API calls to the console. Check the terminal output for debugging information.

## License

This project is part of a resume tailoring system. Use responsibly and in accordance with OpenAI's terms of service.

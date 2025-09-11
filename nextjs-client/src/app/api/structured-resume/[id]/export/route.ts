import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const resumeId = params.id
    const body = await request.json()

    if (!resumeId) {
      return NextResponse.json(
        { error: 'Resume ID is required' },
        { status: 400 }
      )
    }

    // Call the backend API
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/structured-resume/${resumeId}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume_id: resumeId,
        ...body
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: `Backend error: ${errorText}` },
        { status: response.status }
      )
    }

    // For file downloads, we need to handle the response differently
    const contentType = response.headers.get('content-type')
    
    if (contentType && contentType.includes('application/pdf')) {
      const buffer = await response.arrayBuffer()
      return new NextResponse(buffer, {
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': `attachment; filename="resume-${resumeId}.pdf"`,
        },
      })
    } else if (contentType && contentType.includes('text/html')) {
      const html = await response.text()
      return new NextResponse(html, {
        headers: {
          'Content-Type': 'text/html',
          'Content-Disposition': `attachment; filename="resume-${resumeId}.html"`,
        },
      })
    } else {
      const data = await response.json()
      return NextResponse.json(data)
    }

  } catch (error) {
    console.error('Export resume error:', error)
    return NextResponse.json(
      { error: 'Failed to export resume' },
      { status: 500 }
    )
  }
}

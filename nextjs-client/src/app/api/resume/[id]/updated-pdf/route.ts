import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const resumeId = params.id
    
    // Forward the request to the backend
    const response = await fetch(`http://localhost:8000/resume/${resumeId}/updated.html`, {
      method: 'GET',
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Updated HTML not found' },
        { status: 404 }
      )
    }

    // Get the HTML as text
    const htmlText = await response.text()
    
    // Return the HTML with appropriate headers
    return new NextResponse(htmlText, {
      status: 200,
      headers: {
        'Content-Type': 'text/html',
        'Content-Disposition': `inline; filename="resume-${resumeId}-updated.html"`,
      },
    })
    
  } catch (error) {
    console.error('Updated HTML fetch error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

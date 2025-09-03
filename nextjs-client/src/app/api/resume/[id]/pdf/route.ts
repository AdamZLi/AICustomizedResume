import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
      try {
      const resumeId = id;
    
    // Forward the request to the FastAPI backend
    const response = await fetch(`http://localhost:8000/resume/${resumeId}/pdf`);
    
    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || 'PDF not found' },
        { status: response.status }
      );
    }

    // Get the PDF data and headers
    const pdfBuffer = await response.arrayBuffer();
    const contentType = response.headers.get('content-type') || 'application/pdf';
    const contentDisposition = response.headers.get('content-disposition') || 'inline';

    // Return the PDF with proper headers
    return new NextResponse(pdfBuffer, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': contentDisposition,
        'Cache-Control': 'public, max-age=3600',
      },
    });
    
  } catch (error) {
    console.error('PDF fetch error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

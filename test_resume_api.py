#!/usr/bin/env python3
"""
Test script for the Resume API endpoints
"""
import requests
import os
import tempfile

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_resume_upload():
    """Test resume upload with a dummy PDF"""
    try:
        # Create a dummy PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Write minimal PDF content
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000111 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF\n')
            temp_pdf = f.name
        
        # Test upload
        with open(temp_pdf, 'rb') as f:
            files = {'file': ('test_resume.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/resume/upload", files=files)
        
        # Clean up temp file
        os.unlink(temp_pdf)
        
        print(f"Upload test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Upload successful: {data}")
            return data.get('resume_id')
        else:
            print(f"Upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Upload test failed: {e}")
        return None

def test_pdf_view(resume_id):
    """Test PDF viewing endpoint"""
    if not resume_id:
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/resume/{resume_id}/pdf")
        print(f"PDF view test: {response.status_code}")
        if response.status_code == 200:
            print(f"PDF content type: {response.headers.get('content-type')}")
            print(f"PDF size: {len(response.content)} bytes")
            return True
        else:
            print(f"PDF view failed: {response.text}")
            return False
    except Exception as e:
        print(f"PDF view test failed: {e}")
        return False

def test_text_extraction(resume_id):
    """Test text extraction endpoint"""
    if not resume_id:
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/resume/{resume_id}/text")
        print(f"Text extraction test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Text extraction successful: {len(data.get('text', ''))} characters")
            return True
        else:
            print(f"Text extraction failed: {response.text}")
            return False
    except Exception as e:
        print(f"Text extraction test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Resume API endpoints...")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health():
        print("Health check failed, server may not be running")
        return
    
    print("\n" + "=" * 50)
    
    # Test resume upload
    resume_id = test_resume_upload()
    
    if resume_id:
        print("\n" + "=" * 50)
        
        # Test PDF viewing
        test_pdf_view(resume_id)
        
        print("\n" + "=" * 50)
        
        # Test text extraction
        test_text_extraction(resume_id)
    
    print("\n" + "=" * 50)
    print("Testing complete!")

if __name__ == "__main__":
    main()

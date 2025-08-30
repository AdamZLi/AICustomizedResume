#!/usr/bin/env python3
"""
Test script for the Resume Tailoring API
Run this to test the keyword extraction endpoint
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"
KEYWORDS_ENDPOINT = f"{BASE_URL}/keywords_text"

# Sample job descriptions for testing
SAMPLE_JOBS = [
    {
        "name": "Software Engineer",
        "job_text": """
        We are looking for a Software Engineer to join our team. 
        Requirements: Python, JavaScript, React, Node.js, AWS, Docker, 
        Git, REST APIs, SQL, NoSQL databases. Experience with 
        microservices architecture and CI/CD pipelines preferred. 
        Knowledge of machine learning and data analysis is a plus.
        """
    },
    {
        "name": "Data Scientist",
        "job_text": """
        Data Scientist position requiring expertise in Python, R, 
        SQL, pandas, numpy, scikit-learn, TensorFlow, PyTorch. 
        Experience with big data tools like Spark, Hadoop, and 
        cloud platforms (AWS, GCP, Azure). Knowledge of statistics, 
        machine learning algorithms, and data visualization tools.
        """
    },
    {
        "name": "Product Manager",
        "job_text": """
        Product Manager role focusing on user experience, market research, 
        agile methodologies, product strategy, stakeholder management, 
        data analysis, A/B testing, user stories, roadmaps, and 
        cross-functional team leadership. Experience with Jira, 
        Figma, and analytics tools preferred.
        """
    }
]

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Health check failed: Server not running")
        return False
    return True

def test_keywords_extraction(job_data, max_terms=15):
    """Test the keywords extraction endpoint"""
    payload = {
        "job_text": job_data["job_text"],
        "max_terms": max_terms
    }
    
    try:
        print(f"\n🔍 Testing: {job_data['name']}")
        print(f"   Max terms: {max_terms}")
        
        response = requests.post(KEYWORDS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: {response.status_code}")
            print(f"   Keywords ({len(result['keywords'])}): {result['keywords'][:5]}...")
            print(f"   Skills ({len(result['skills'])}): {result['skills'][:5]}...")
            print(f"   Tools ({len(result['tools'])}): {result['tools'][:5]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed: Server not running")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

def test_error_handling():
    """Test error handling with invalid inputs"""
    print(f"\n🚨 Testing Error Handling:")
    
    # Test empty job text
    try:
        response = requests.post(KEYWORDS_ENDPOINT, json={"job_text": "", "max_terms": 10})
        print(f"   Empty text: {response.status_code} - {response.json().get('detail', '')}")
    except Exception as e:
        print(f"   Empty text: Error - {e}")
    
    # Test invalid max_terms
    try:
        response = requests.post(KEYWORDS_ENDPOINT, json={"job_text": "test", "max_terms": 0})
        print(f"   Invalid max_terms: {response.status_code} - {response.json().get('detail', '')}")
    except Exception as e:
        print(f"   Invalid max_terms: Error - {e}")

def main():
    """Main test function"""
    print("🧪 Resume Tailoring API Test Suite")
    print("=" * 50)
    
    # Test health check first
    if not test_health_check():
        print("\n💡 Make sure to start the server first:")
        print("   python main.py")
        return
    
    # Test keyword extraction with different job descriptions
    for job in SAMPLE_JOBS:
        test_keywords_extraction(job, max_terms=15)
    
    # Test error handling
    test_error_handling()
    
    print(f"\n🎯 Test completed! Check the results above.")
    print(f"   API documentation available at: {BASE_URL}/docs")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script for the Cotton Weed Detection API
Use this to test your API endpoints directly
"""
import requests
import sys
from pathlib import Path

API_URL = "https://cotton-weed-api.onrender.com"

def test_health():
    """Test the health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_root():
    """Test the root endpoint"""
    print("\nTesting / endpoint...")
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_test_endpoint():
    """Test the /test endpoint"""
    print("\nTesting /test endpoint...")
    try:
        response = requests.get(f"{API_URL}/test", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_predict(image_path=None):
    """Test the /predict endpoint"""
    print("\nTesting /predict endpoint...")

    if image_path is None:
        print("No image provided. Skipping predict test.")
        print("Usage: python test_api.py path/to/image.jpg")
        return False

    if not Path(image_path).exists():
        print(f"Error: Image not found at {image_path}")
        return False

    try:
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/jpeg')}
            print(f"Uploading image: {image_path}")

            # Increase timeout for prediction (model inference takes time)
            response = requests.post(
                f"{API_URL}/predict",
                files=files,
                timeout=60  # 60 second timeout
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"Success! Found {result['num_detections']} detections")
                print(f"Response: {result}")
                return True
            else:
                print(f"Error Response: {response.text}")
                return False

    except requests.exceptions.Timeout:
        print("Error: Request timed out after 60 seconds")
        print("This might indicate the API is under heavy load or crashed")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Cotton Weed Detection API Test Suite")
    print("=" * 60)

    results = []

    # Test basic endpoints
    results.append(("Health Check", test_health()))
    results.append(("Root Endpoint", test_root()))
    results.append(("Test Endpoint", test_test_endpoint()))

    # Test predict endpoint if image provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        results.append(("Predict Endpoint", test_predict(image_path)))
    else:
        print("\n" + "=" * 60)
        print("To test the /predict endpoint, provide an image path:")
        print(f"  python {sys.argv[0]} path/to/image.jpg")
        print("=" * 60)

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    # Exit with appropriate code
    if all(result[1] for result in results):
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)

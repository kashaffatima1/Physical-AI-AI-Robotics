"""
Test script for the Physical AI Book features
This script tests all the implemented features:
1. Authentication system
2. Personalization features
3. Urdu translation
4. Subagents functionality
"""
import requests
import json
import uuid

# Configuration
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json"}

def test_auth():
    """Test authentication functionality"""
    print("Testing Authentication System...")

    # Generate unique email for test
    test_email = f"testuser_{uuid.uuid4()}@example.com"
    test_password = "SecurePassword123!"
    software_exp = "Experienced in Python, JavaScript, and React"
    hardware_exp = "Familiar with Arduino, Raspberry Pi, and basic electronics"

    print(f"Signing up user: {test_email}")

    # Test signup
    signup_data = {
        "email": test_email,
        "password": test_password,
        "software_experience": software_exp,
        "hardware_experience": hardware_exp
    }

    response = requests.post(f"{BASE_URL}/api/auth/signup",
                            headers=HEADERS,
                            data=json.dumps(signup_data))

    if response.status_code == 200:
        print("✓ Signup successful")
        result = response.json()
        user_id = result["user_id"]
        session_token = result["session_token"]
        print(f"User ID: {user_id}")
    else:
        print(f"✗ Signup failed: {response.text}")
        return None, None

    # Test signin
    signin_data = {
        "email": test_email,
        "password": test_password
    }

    response = requests.post(f"{BASE_URL}/api/auth/signin",
                            headers=HEADERS,
                            data=json.dumps(signin_data))

    if response.status_code == 200:
        print("✓ Signin successful")
        result = response.json()
        user_id = result["user_id"]
        session_token = result["session_token"]
    else:
        print(f"✗ Signin failed: {response.text}")
        return None, None

    # Test profile retrieval
    profile_headers = {"user-id": user_id}
    response = requests.post(f"{BASE_URL}/api/auth/profile",
                            headers=profile_headers)

    if response.status_code == 200:
        print("✓ Profile retrieval successful")
        result = response.json()
        print(f"Retrieved profile for user: {result['user_id']}")
    else:
        print(f"✗ Profile retrieval failed: {response.text}")

    return user_id, session_token

def test_personalization(user_id):
    """Test personalization features"""
    print("\nTesting Personalization Features...")

    chapter_id = "introduction-to-physical-ai"

    # Set personalization preferences
    personalization_data = {
        "language": "en",
        "difficulty": 2,
        "hide_advanced": False,
        "hide_code": True
    }

    headers = {
        "Content-Type": "application/json",
        "user-id": user_id,
        "chapter-id": chapter_id
    }

    response = requests.post(f"{BASE_URL}/api/auth/personalize",
                            headers=headers,
                            data=json.dumps(personalization_data))

    if response.status_code == 200:
        print("✓ Personalization settings saved successfully")
    else:
        print(f"✗ Personalization save failed: {response.text}")
        return False

    # Get personalization preferences
    response = requests.post(f"{BASE_URL}/api/auth/get-personalize",
                            headers=headers)

    if response.status_code == 200:
        print("✓ Personalization settings retrieved successfully")
        result = response.json()
        print(f"Retrieved preferences: {result}")
    else:
        print(f"✗ Personalization retrieval failed: {response.text}")
        return False

    return True

def test_urdu_translation():
    """Test Urdu translation functionality"""
    print("\nTesting Urdu Translation...")

    text_to_translate = "Physical AI is an interdisciplinary field combining robotics, machine learning, and physics."

    translation_data = {
        "text": text_to_translate
    }

    response = requests.post(f"{BASE_URL}/api/auth/translate-to-urdu",
                            headers=HEADERS,
                            data=json.dumps(translation_data))

    if response.status_code == 200:
        print("✓ Urdu translation successful")
        result = response.json()
        print(f"Original: {result['original_text']}")
        print(f"Translated: {result['translated_text']}")
    else:
        print(f"✗ Urdu translation failed: {response.text}")
        return False

    return True

def test_subagents():
    """Test subagents functionality"""
    print("\nTesting Subagents...")

    # Test knowledge retrieval
    query_data = {
        "query": "What is reinforcement learning in robotics?",
        "context": None,
        "preferred_subagent": "knowledge"
    }

    response = requests.post(f"{BASE_URL}/api/subagents/query",
                            headers=HEADERS,
                            data=json.dumps(query_data))

    if response.status_code == 200:
        print("✓ Subagent query successful")
        result = response.json()
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Subagent used: {result['subagent_used']}")
        print(f"Confidence: {result['confidence']}")
    else:
        print(f"✗ Subagent query failed: {response.text}")
        return False

    # Test explanation subagent
    query_data = {
        "query": "Explain neural networks in simple terms",
        "context": None,
        "preferred_subagent": "explanation"
    }

    response = requests.post(f"{BASE_URL}/api/subagents/query",
                            headers=HEADERS,
                            data=json.dumps(query_data))

    if response.status_code == 200:
        print("✓ Explanation subagent query successful")
        result = response.json()
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Subagent used: {result['subagent_used']}")
    else:
        print(f"✗ Explanation subagent query failed: {response.text}")
        return False

    return True

def main():
    """Main test function"""
    print("Starting tests for Physical AI Book features...\n")

    # Test authentication
    user_id, session_token = test_auth()
    if not user_id:
        print("Authentication tests failed, stopping...")
        return

    # Test personalization
    if not test_personalization(user_id):
        print("Personalization tests failed")

    # Test Urdu translation
    if not test_urdu_translation():
        print("Urdu translation tests failed")

    # Test subagents
    if not test_subagents():
        print("Subagents tests failed")

    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
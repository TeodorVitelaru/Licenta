"""
Test Script - Verifica backend endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check"""
    print("\n Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_register():
    """Test registrare user"""
    print("\n Testing /auth/register endpoint...")
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✓ Token: {token[:50]}...")
        return token
    else:
        print(f"Response: {response.text}")
        return None


def test_login(email, password):
    """Test login"""
    print("\n Testing /auth/login endpoint...")
    login_data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"Response: {response.text}")
        return None


def test_get_profile(token):
    """Test get user profile"""
    print("\n Testing /users/me endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_predict(token):
    """Test predictie match"""
    print("\n Testing /predict endpoint...")

    match_data = {
        "minute": 45,
        "score_home": 1,
        "score_away": 0,
        "xg_home": 1.5,
        "xg_away": 0.8,
        "shots_home": 5,
        "shots_away": 3,
        "shots_on_target_home": 3,
        "shots_on_target_away": 1,
        "passes_home": 350,
        "passes_away": 250,
        "pressure_home": 65,
        "pressure_away": 35,
        "match_id": "test_match_001"
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/predict",
                             json=match_data, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        pred = response.json()
        print(f" Prediction received:")
        print(f"  - Match ID: {pred.get('match_id')}")
        print(f"  - Minute: {pred.get('minute')}")
        print(f"  - Outcome: {pred.get('predicted_outcome')}")
        print(f"  - Confidence: {pred.get('confidence'):.2%}")
        print(f"  - Probabilities: {pred.get('probabilities')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_get_matches(token):
    """Test citire predictii"""
    print("\n Testing /matches endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/matches", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        matches = response.json()
        print(f" Found {len(matches)} predictions")
        for m in matches:
            print(f"  - {m.get('match_id')} @ minute {m.get('minute')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def run_all_tests():
    """Ruleaza toate testurile"""
    print("=" * 80)
    print(" BACKEND TESTS - Win Probability API")
    print("=" * 80)

    # Health check
    if not test_health():
        print("\n Health check failed! Server nu rula?")
        return

    # Register
    token = test_register()
    if not token:
        print("\n Register failed!")
        return

    # Get profile
    if not test_get_profile(token):
        print("\n Get profile failed!")
        return

    # Predict
    if not test_predict(token):
        print("\n Predict failed!")
        return

    # Get matches
    if not test_get_matches(token):
        print("\n Get matches failed!")
        return

    print("\n" + "=" * 80)
    print(" ALL TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    print("Make sure server is running: python main.py")
    input("Press Enter to start tests...")
    run_all_tests()

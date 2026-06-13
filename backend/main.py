"""
Entry Point - Rulează backend FastAPI
"""
from config import RAPIDAPI_KEY, RAPIDAPI_HOST
import uvicorn
import sys
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Adauga backend la path
sys.path.insert(0, str(Path(__file__).parent))


def test_rapidapi_fixtures_events(fixture_id: int = 123456):
    """
    Test API call to RapidAPI - Fixtures Events endpoint
    """
    print("\n" + "=" * 80)
    print(
        f"🔍 Testing RapidAPI Fixtures Events Endpoint (fixture_id={fixture_id})")
    print("=" * 80 + "\n")

    url = f"https://{RAPIDAPI_HOST}/v3/fixtures/events?fixture={fixture_id}"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }

    if not RAPIDAPI_KEY:
        print("⚠️  RAPIDAPI_KEY nu este setat în .env!")
        print("   Adauga aceasta linie in .env:")
        print("   RAPIDAPI_KEY=your_rapidapi_key_here\n")
        return

    try:
        req = Request(url, headers=headers)
        response = urlopen(req, timeout=10)
        data = json.loads(response.read().decode('utf-8'))

        print(f"✅ Response Status: {response.status}")
        print(f"✅ Response Headers: Content-Type: application/json")
        print("\n📊 API Response:\n")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("\n" + "=" * 80 + "\n")

    except HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            print(f"   Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Response: {e.read().decode('utf-8')}")
    except URLError as e:
        print(f"❌ URL Error: {e.reason}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    print("=" * 80)
    print("🚀 WIN PROBABILITY PREDICTION API - Backend Server")
    print("=" * 80)
    print("\n📍 Server URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔍 ReDoc: http://localhost:8000/redoc")
    print("\n⚠️  Asigura-te că modelul ML e disponibil în ../model_3_clase/")

    # Ruleaza uvicorn server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

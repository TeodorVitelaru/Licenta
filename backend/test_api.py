"""
Script simplu de test pentru API-Football (API-Sports).
"""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import API_FOOTBALL_BASE_URL, API_FOOTBALL_KEY


def get_fixture_statistics(fixture_id: int) -> dict:
    if not API_FOOTBALL_KEY:
        raise ValueError("API_FOOTBALL_KEY nu este setat in .env")

    endpoint = "/fixtures/statistics"
    query = urlencode({"fixture": fixture_id})
    url = f"{API_FOOTBALL_BASE_URL}{endpoint}?{query}"

    request = Request(
        url,
        headers={
            "x-apisports-key": API_FOOTBALL_KEY,
        },
        method="GET",
    )

    with urlopen(request, timeout=20) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload)


def print_summary(data: dict) -> None:
    response_items = data.get("response", [])
    if not response_items:
        print("Nu exista statistici in raspuns pentru fixture-ul dat.")
        return

    print("\nStatistici pe echipe:")
    for item in response_items:
        team = item.get("team") or {}
        stats = item.get("statistics") or []
        print(f"\nteam={team.get('name')}")
        for stat in stats:
            stat_type = stat.get("type")
            stat_value = stat.get("value")
            print(f"- {stat_type}: {stat_value}")


if __name__ == "__main__":
    selected_fixture_id = 215662

    print("API-Football fixture statistics test start")
    print(f"base_url={API_FOOTBALL_BASE_URL}")
    print(f"fixture={selected_fixture_id}")

    try:
        statistics_data = get_fixture_statistics(selected_fixture_id)
        print("\nStatus: success")
        print("\nJSON raw:")
        print(json.dumps(statistics_data, indent=2, ensure_ascii=False))
        print_summary(statistics_data)
    except HTTPError as exc:
        print(f"HTTP Error {exc.code}: {exc.reason}")
        try:
            error_payload = exc.read().decode("utf-8")
            print(error_payload)
        except Exception:
            pass
    except URLError as exc:
        print(f"URL Error: {exc.reason}")
    except Exception as exc:
        print(f"Error: {type(exc).__name__}: {exc}")

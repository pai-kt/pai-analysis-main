"""GPS·행정구역 기반 현재 외기기온 조회 (Open-Meteo, API 키 불필요)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from functools import lru_cache


def _fetch_json(url: str, timeout: int = 10):
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "A-DIMS/1.0 (smart-farm decision support; contact: local)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_current_temperature(lat: float, lon: float) -> float | None:
    """위·경도 기준 현재 기온(℃) — Open-Meteo forecast API."""
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m",
            "timezone": "auto",
        }
    )
    data = _fetch_json(f"https://api.open-meteo.com/v1/forecast?{params}")
    if not data:
        return None
    try:
        return float(data["current"]["temperature_2m"])
    except (KeyError, TypeError, ValueError):
        return None


def reverse_geocode_label(lat: float, lon: float) -> str:
    """좌표 → 행정구역·지명 (한국어, OpenStreetMap Nominatim)."""
    params = urllib.parse.urlencode(
        {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "accept-language": "ko",
            "zoom": 10,
        }
    )
    data = _fetch_json(f"https://nominatim.openstreetmap.org/reverse?{params}")
    if not data:
        return f"위도 {lat:.4f} · 경도 {lon:.4f}"
    addr = data.get("address") or {}
    parts = [
        addr.get("city") or addr.get("county") or addr.get("state"),
        addr.get("borough") or addr.get("town") or addr.get("village") or addr.get("suburb"),
    ]
    label = " ".join(p for p in parts if p)
    return label or data.get("display_name", f"위도 {lat:.4f} · 경도 {lon:.4f}")


def geocode_korean_region(sido: str, sigungu: str) -> tuple[float, float] | None:
    """시·도 + 시·군·구 → 위·경도 (Nominatim)."""
    query = f"{sigungu}, {sido}, South Korea"
    params = urllib.parse.urlencode(
        {
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "kr",
        }
    )
    results = _fetch_json(f"https://nominatim.openstreetmap.org/search?{params}")
    if not results:
        return None
    try:
        hit = results[0]
        return float(hit["lat"]), float(hit["lon"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


@lru_cache(maxsize=512)
def fetch_outdoor_temp_for_region(sido: str, sigungu: str) -> tuple[float | None, str | None]:
    """선택한 행정구역의 현재 외기기온(℃)."""
    coords = geocode_korean_region(sido, sigungu)
    if not coords:
        return None, None
    lat, lon = coords
    temp = fetch_current_temperature(lat, lon)
    label = f"{sido} {sigungu}"
    return temp, label

"""대한민국 시·도 / 시·군·구 행정구역 목록."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / "data" / "korea_admin_district.json"


@lru_cache(maxsize=1)
def load_korea_regions() -> dict[str, list[str]]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    regions: dict[str, list[str]] = {}
    for item in payload["data"]:
        for sido, sigungu_list in item.items():
            if not sigungu_list and sido == "세종특별자치시":
                regions[sido] = ["세종시"]
            else:
                regions[sido] = list(sigungu_list)
    return regions


def list_sido() -> list[str]:
    return list(load_korea_regions().keys())


def list_sigungu(sido: str) -> list[str]:
    return list(load_korea_regions().get(sido, []))

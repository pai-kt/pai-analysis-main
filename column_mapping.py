"""환경센서 CSV 컬럼 자동 매핑."""

EXTERNAL_CUMULATIVE_SOLAR_CANDIDATES = [
    "외부누적 일사량",
    "외부누적일사량",
    "외부누적_일사량",
    "누적일사량_외부",
    "external_cumulative_solar",
]


def pick_column_index(columns, candidates, fallback=0):
    cols = list(columns)
    for name in candidates:
        if name in cols:
            return cols.index(name)
    for name in candidates:
        for i, col in enumerate(cols):
            if name in str(col):
                return i
    return fallback if fallback < len(cols) else 0


def is_external_cumulative_solar_column(col) -> bool:
    c = str(col)
    if "내부" in c:
        return False
    cl = c.lower()
    if "internal" in cl and "external" not in cl:
        return False
    if ("외부" in c or "external" in cl) and ("누적" in c or "cumulative" in cl):
        return "일사" in c or "solar" in cl or "광" in c
    if "누적일사량_외부" in c or "누적일사량(외부" in c:
        return True
    return False


def list_external_cumulative_solar_columns(columns):
    return [c for c in columns if is_external_cumulative_solar_column(c)]


def pick_external_cumulative_solar_index(columns, fallback=None):
    cols = list(columns)
    matched = [i for i, c in enumerate(cols) if is_external_cumulative_solar_column(c)]
    if matched:
        for name in EXTERNAL_CUMULATIVE_SOLAR_CANDIDATES:
            for i in matched:
                if name in str(cols[i]):
                    return i
        return matched[0]
    for name in EXTERNAL_CUMULATIVE_SOLAR_CANDIDATES:
        idx = pick_column_index(cols, [name], fallback=-1)
        if idx >= 0 and is_external_cumulative_solar_column(cols[idx]):
            return idx
    if fallback is not None and 0 <= fallback < len(cols):
        return fallback
    return pick_column_index(cols, EXTERNAL_CUMULATIVE_SOLAR_CANDIDATES)


def pick_external_cumulative_solar_column(columns):
    idx = pick_external_cumulative_solar_index(columns)
    return list(columns)[idx]

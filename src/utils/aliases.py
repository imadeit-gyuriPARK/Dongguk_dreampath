"""학교명 약어(연대, 건대 등) -> 정식명 별칭 매핑.

매핑 데이터 자체는 data/processed/school_aliases.csv(약어,정식명)에 수작업으로 관리하고,
이 모듈은 그걸 불러와서 찾아보는 역할만 함.
"""

from pathlib import Path

import pandas as pd

ALIASES_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "school_aliases.csv"


def load_aliases(path: Path = ALIASES_PATH) -> dict[str, str]:
    """약어 -> 정식명 딕셔너리로 로드."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    return dict(zip(df["약어"], df["정식명"]))


def resolve_alias(token: str, aliases: dict[str, str]) -> str | None:
    """token이 등록된 약어면 정식명을, 아니면 None을 반환."""
    return aliases.get(token)

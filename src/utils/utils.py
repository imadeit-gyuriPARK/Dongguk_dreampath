"""노트북들이 공통으로 쓰는 헬퍼 함수 모음."""

from pathlib import Path

from preprocessing import expand_school_suffix


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "src").is_dir() and (p / "data").is_dir():
            return p
    raise FileNotFoundError("repo 루트를 못 찾았어요 (data/, src/ 폴더 기준)")


def preprocess_candidate(candidate_text: str, alias_to_canonical: dict) -> str:
    """school_candidate의 각 토큰을 정식 학교명 형태로 통일.
    GT 약어에 있으면 그 정식명으로, 아니면 접미사 확장(초/고->등학교, 중->학교, 대->학교)."""
    tokens = []
    for tok in candidate_text.split():
        if tok in alias_to_canonical:
            tokens.append(alias_to_canonical[tok])
        else:
            tokens.append(expand_school_suffix(tok)[0])
    return " ".join(tokens)


def gt_match(expanded_text: str, gt_names: set) -> str:
    return " ".join(tok for tok in expanded_text.split() if tok in gt_names)


def apply_token_fixes(candidates: str, token_fixes: dict, junk_tokens: set) -> str:
    """알려진 표기 오류(token_fixes)를 보정하고, 순수 오검출(junk_tokens)만 제외."""
    kept = [token_fixes.get(tok, tok) for tok in candidates.split()]
    kept = [tok for tok in kept if tok not in junk_tokens]
    return " ".join(kept)

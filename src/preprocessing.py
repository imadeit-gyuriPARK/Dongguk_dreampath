"""댓글 텍스트 전처리 단계별 함수 모음."""

import re

from konlpy.tag import Okt

_okt = Okt()

# 이모지 유니코드 범위 (이모티콘, 심볼/픽토그램, 교통, 부속 심볼, 깃발 등)
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "️"
    "]+"
)

# ㅋㅋㅋ, ㅎㅎ, ㅠㅠ, ㅜㅜ 처럼 완성되지 않은 자음/모음만 연속되는 구간
_JAMO_PATTERN = re.compile(r"[ㄱ-ㅎㅏ-ㅣ]+")

# 마침표, 느낌표, 물음표, 물결, 말줄임표, 슬래시 등 문장부호 (반복 포함: .. !! 등)
_PUNCT_PATTERN = re.compile(r"[.,!?~…/]+")


def remove_emoji(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text)


def remove_jamo_only(text: str) -> str:
    return _JAMO_PATTERN.sub("", text)


def remove_punct(text: str) -> str:
    return _PUNCT_PATTERN.sub(" ", text)


# (), [], {} 및 그 안의 내용 (예: "인제대학교(김해)" -> "인제대학교")
_BRACKET_PATTERN = re.compile(r"[(\[{].*?[)\]}]")


def strip_brackets(text: str) -> str:
    """괄호류와 그 안의 내용을 지우고, 공백도 전부 제거 (학교명 정규화용)."""
    text = _BRACKET_PATTERN.sub("", text)
    text = re.sub(r"\s+", "", text)
    return text.strip()


def clean_text(text: str) -> str:
    """1단계 전처리: 이모지 / ㅋㅋ,ㅎㅎ,ㅠㅠ류 / 문장부호 제거 후 공백 정리."""
    text = remove_emoji(text)
    text = remove_jamo_only(text)
    text = remove_punct(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_nouns(text: str) -> str:
    """2단계 전처리: 조사/동사/형용사 등을 버리고 명사만 남김 (원형 복원 없음).

    같은 명사가 한 댓글 안에 여러 번 나오면 처음 등장한 순서만 남기고 중복 제거.
    """
    tokens = _okt.pos(text)
    nouns = [word for word, tag in tokens if tag == "Noun"]
    unique_nouns = list(dict.fromkeys(nouns))
    return " ".join(unique_nouns)


def preprocess(text: str) -> str:
    """전체 파이프라인: 이모지/ㅋㅋㅎㅎ/문장부호 제거 → 조사/동사 제거(명사만 추출)."""
    return extract_nouns(clean_text(text))


_SCHOOL_SUFFIX = re.compile(r"(초|중|고|대|학교)$")


def noun_count(noun_text: str) -> int:
    """명사 중 초/중/고/대/학교로 끝나는 토큰 개수 (학교명 후보 개수 가설 검증용)."""
    return sum(1 for token in noun_text.split() if _SCHOOL_SUFFIX.search(token))

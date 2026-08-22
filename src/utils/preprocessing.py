"""댓글 텍스트 전처리 단계별 함수 모음."""

import os
import re

# konlpy(Okt)가 JVM을 못 찾는 환경(JAVA_HOME 갱신 전에 켜진 커널 등)을 위한 안전장치
os.environ.setdefault(
    "JAVA_HOME", r"C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot"
)

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

# 마침표, 느낌표, 물음표, 물결, 말줄임표, 슬래시, 해시태그(#) 등 문장부호 (반복 포함: .. !! 등)
_PUNCT_PATTERN = re.compile(r"[.,!?~…/#]+")


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


_DROP_TAGS = {"Verb", "Adjective", "Punctuation", "KoreanParticle"}

# 흔히 쓰이는 조사만 모음 (긴 것부터 검사해야 "에서"가 "에"로 잘못 잘리는 일이 없음)
_JOSA_SUFFIXES = sorted(
    [
        "에서", "으로", "한테", "에게", "부터", "까지", "이랑", "이나", "이라",
        "은", "는", "이", "가", "을", "를", "에", "로", "와", "과", "도", "만", "의", "랑", "나", "께",
    ],
    key=len,
    reverse=True,
)


def _recover_from_josa(word: str) -> str:
    """Okt가 명사 일부까지 통째로 Josa로 잘못 태깅한 경우(예: '건국대로' -> '건국'+'대로')
    조사 부분만 떼어내고 남은 앞부분을 복구. 순수 조사(은/는/이/가 등)면 빈 문자열 반환."""
    for josa in _JOSA_SUFFIXES:
        if len(word) > len(josa) and word.endswith(josa):
            return word[: -len(josa)]
    return ""


def clean_pos(text: str) -> str:
    """2단계 전처리: 명사만 뽑는 게 아니라 조사/동사/형용사만 지움 (원형 복원 없음).

    - 어절(공백 기준 단어) 단위로 분석해서, 조사/동사/형용사가 아닌 나머지 토큰만
      공백 없이 그대로 이어붙임. "대치"+"중"(Suffix)이나 "서초"+"초"(Noun) 처럼
      Okt가 학교명 축약어를 여러 조각으로 쪼개도, 조사/동사가 아니면 지우지 않으니
      원문 그대로 "대치중"/"서초초"가 유지됨.
    - Josa 태그 토큰은 무조건 버리는 게 아니라 `_recover_from_josa`로 한 번 더 확인해서,
      "대로"처럼 명사 일부가 조사에 붙어 같이 태깅된 경우 그 앞부분("대")을 복구.
    - 같은 단어가 한 댓글 안에 여러 번 나오면 처음 등장한 순서만 남기고 중복 제거.
    """
    words = []
    for eojeol in text.split():
        buf = ""
        for word, tag in _okt.pos(eojeol):
            if tag == "Josa":
                buf += _recover_from_josa(word)
            elif tag not in _DROP_TAGS:
                buf += word
        if buf:
            words.append(buf)
    unique_words = list(dict.fromkeys(words))
    return " ".join(unique_words)


def preprocess(text: str) -> str:
    """전체 파이프라인: 이모지/ㅋㅋㅎㅎ/문장부호 제거 → 조사/동사 제거."""
    return clean_pos(clean_text(text))


_SCHOOL_SUFFIXES = ("학교", "초", "중", "고", "대")


def extract_school_candidates(noun_text: str) -> str:
    """초/중/고/대/학교로 끝나는 토큰만 뽑아 공백으로 이어붙임 (해당 댓글의 학교명 후보/대표값).

    comment_noun(clean_pos까지 끝낸 결과) 기준으로 검사. clean_pos 단계에서
    이미 조사 복구(_recover_from_josa)를 거쳤기 때문에 "건국대로" 같은 경우도
    comment_noun에는 "건국대"로 남아있어서 정상적으로 잡힘.
    """
    return " ".join(token for token in noun_text.split() if token.endswith(_SCHOOL_SUFFIXES))


def noun_count(noun_text: str) -> int:
    """학교명 후보 개수 (댓글당 학교 1개 가설 검증용)."""
    return len(extract_school_candidates(noun_text).split())


def extract_school_candidates_fallback(clean_text_1: str) -> str:
    """school_candidate_count == 0인 행을 위한 폴백.

    comment_noun(Okt 결과)이 아니라 comment_clean_1(1단계, Okt 타기 전 원문)에서
    어절 단위로 직접 문자열 매칭해서 초/중/고/대/학교로 끝나는 가장 짧은 부분 문자열을 찾음.
    Okt가 접미사를 조사/다른 명사에 흡수시켜버려 comment_noun에서 놓친 후보를 복구하는 용도.
    조사 축약형이나 오검출이 섞여 나올 수 있지만, 그건 이후 단계에서 별도로 걸러짐.
    """
    candidates = []
    for eojeol in clean_text_1.split():
        for i in range(2, len(eojeol) + 1):
            prefix = eojeol[:i]
            if prefix.endswith(_SCHOOL_SUFFIXES):
                candidates.append(prefix)
                break
    unique_candidates = list(dict.fromkeys(candidates))
    return " ".join(unique_candidates)


def extract_school_candidates_longest(clean_text_1: str) -> str:
    """extract_school_candidates_fallback의 가장 긴 접미사 매칭 버전.

    기존 함수는 어절 안에서 초/중/고/대/학교로 끝나는 가장 "짧은" 부분 문자열을 찾다 보니,
    "서초중"처럼 짧은 유효 접미사("서초")가 먼저 걸려서 뒤에 이어지는 "중"을 놓치는 경우가 있음
    (merge_spaced_syllables로 붙여쓴 긴 학교명을 복구할 때 특히 문제가 됨: "이대부초"->"이대"처럼).
    그래서 어절 길이부터 거꾸로 줄여가며 가장 "긴" 부분 문자열을 우선 채택.
    기존 extract_school_candidates_fallback을 쓰는 3.0의 원래 파이프라인에는 영향 없도록
    별도 함수로 분리함."""
    candidates = []
    for eojeol in clean_text_1.split():
        for i in range(len(eojeol), 1, -1):
            prefix = eojeol[:i]
            if prefix.endswith(_SCHOOL_SUFFIXES):
                candidates.append(prefix)
                break
    unique_candidates = list(dict.fromkeys(candidates))
    return " ".join(unique_candidates)


def merge_spaced_syllables(text: str) -> str:
    """'서 강 대'처럼 한 글자씩 띄어 쓴 경우, 연속된 한 글자 토큰들을 하나로 합침
    (예: '서 강 대 치킨' -> '서강대 치킨'). count.ipynb에서 count==0 폴백으로도
    못 잡힌 행들을 위한 추가 폴백 전처리 — clean_text 기본 파이프라인에는 포함 안 함."""
    tokens = text.split(" ")
    merged = []
    buf = ""
    for tok in tokens:
        if len(tok) == 1 and "가" <= tok <= "힣":
            buf += tok
        else:
            if buf:
                merged.append(buf)
                buf = ""
            merged.append(tok)
    if buf:
        merged.append(buf)
    return " ".join(merged)


_SUFFIX_EXPAND = {"초": "등학교", "중": "학교", "고": "등학교", "대": "학교"}


def expand_school_suffix(candidate: str) -> list[str]:
    """축약된 학교명 후보를 정식 명칭 형태(들)로 확장 (GT 대조용, 우선순위 순서로 반환).

    - 이미 "학교"로 끝나면 그대로 하나만 반환
    - "초"/"고"는 "등학교", "중"은 "학교"를 붙임
    - "대"는 "학교"(대학교)를 우선 시도하고, 매칭 실패 시를 대비해 "학"(전문대/기능대,
      예: "폴리텍대"->"폴리텍대학")도 후보로 같이 반환
    """
    if candidate.endswith("학교"):
        return [candidate]
    last = candidate[-1]
    if last == "대":
        return [candidate + "학교", candidate + "학"]
    return [candidate + _SUFFIX_EXPAND.get(last, "")]

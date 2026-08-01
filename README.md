
## 파이프라인

### 0. GT(정답) 사전 데이터 준비 — `src/gt/build_school_dict.ipynb`, `src/gt/build_abbreviations.ipynb`

- `build_school_dict.ipynb`: 공공데이터포털의 초중고(`High_Middle_Elementary.csv`,
  10,470개) + 대학교(`University.csv`, 1,969개) 명단을 정리해
  `data/processed/gt_schoolnames.csv`로 저장.
- `build_abbreviations.ipynb`: 하드코딩 (약어 규칙으로 넣을려고 했지만 실패)
  `gt_schoolnames.csv`에 `약어`(수동 예외,한 번 채우면 덮어쓰지 않음) 컬럼을 추가.

### 1. EDA — `src/eda.ipynb`
`data/raw/dataset.csv`(1,000건) 확인. 결측치는 없고, `comment` 완전 중복이 173개 고유
문구(최대 6회 반복)로 발견됨 — 친구에게 문구를 그대로 공유해 신청한 경우로 보여
오류로 판단하지 않음. 학교명이 문장 속에 자연어로 섞여 있고 "건국대→건대" 같은
축약형이 존재한다는 걸 확인해, "초/중/고/대/학교 접미사로 판별"하는 방향을 정함.

### 2.1 전처리 1단계 — `clean_text` (`preprocessing.py`)
이모지, `ㅋㅋ`/`ㅎㅎ`/`ㅠㅠ`류 자음·모음만 연속되는 구간, 문장부호(`. , ! ? ~ … /`)를
제거하고 공백을 정리 → `comment_clean_1`.

### 2.2 전처리 2단계 — `extract_nouns` (`preprocessing.py`)

- 명사 추출하다가 오류 발생 -> 조사만 삭제하는걸로 변경

어절(공백 기준 단어) 단위로 Okt 형태소 분석을 돌려서,
- `Josa`(조사)로 태깅된 토큰은 무조건 버리는 게 아니라 `_recover_from_josa`를 거침 — 알려진
  조사 접미사(은/는/이/가/에서/으로 등)로 끝나면 그 부분만 잘라내고 앞부분(예: "건국대**로**"
  → "건국대")은 살림. 순수 조사면 빈 문자열.

전처리 1·2단계 결과를 `data/processed/preprocessing.csv`에
`comment_id, comment, comment_clean_1, comment_noun`로 저장 (`src/preprocessing.ipynb`).

### 4. 1차 필터 — 학교명 후보 추출 (`src/count.ipynb`)
`comment_noun`에서 "학교/초/중/고/대" 접미사로 끝나는 토큰만 뽑아 `school_candidate`로
만듦 (`extract_school_candidates`). 이 시점에 댓글당 후보 개수 분포:

| 후보 개수 | 댓글 수 |
|---|---|
| 0 | 109 |
| 1 | 790 |
| 2 | 83 |
| 3 | 18 |

### 5. 2차 필터 — 후보 0건 폴백 (`src/count.ipynb`)

후보가 0건인 109개 행을 두 단계 폴백으로 복구:

1. **원문 재매칭**: Okt가 학교명을 조사/다른 명사에 흡수시켜 사라진 경우, 형태소 분석
   이전 원문(`comment_clean_1`)에서 어절 단위로 직접 접미사 매칭 재시도
   (`extract_school_candidates_fallback`). 109건 → 3건으로 감소.
2. **띄어쓴 음절 병합**: "서 강 대"처럼 한 글자씩 띄어 쓴 나머지 3건은 연속된 한 글자
   토큰을 합친 뒤(`merge_spaced_syllables`) 같은 폴백을 한 번 더 적용. 0건 완전 해소.

최종 결과를 `data/processed/school_candidate_counts.csv`에
`comment_id, comment, comment_clean_1, comment_noun, school_candidate, school_candidate_count`로
저장.

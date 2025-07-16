# CPA 시험 파일 다운로드 도구

이 도구는 금융감독원 공인회계사 시험 게시판에서 기출문제 파일을 자동으로 다운로드합니다.

## 구성 요소

### 1. process_01_get_post_urls.py
게시판의 게시물 URL 목록을 수집합니다.
- 출력: `01_post_urls_cache.csv`

### 2. process_02_get_file_urls.py
각 게시물에서 첨부파일 URL을 추출합니다.
- 입력: `01_post_urls_cache.csv`
- 출력: `02_file_urls_cache.csv`

### 3. 파일 다운로드 (3가지 방법)

#### 방법 1: process_03_downloadfiles.py (기본)
모든 파일을 일괄 다운로드합니다.
- 저장 위치: `download/`
- 파일명 형식: `{연도}_{차수}_{원본파일명}`

```bash
python process_03_downloadfiles.py
```

#### 방법 2: process_03_v2_organized.py (과목별 정리)
과목별로 폴더를 나누어 다운로드할 수 있습니다.

**특징:**
- 과목별 자동 분류 (경영학, 경제학, 상법, 세법, 회계학 등)
- 확정답안/가답안 구분
- 실행 시간 기반 폴더명으로 충돌 방지

**저장 구조:**
```
download/
└── 20250111_143022_2차_원가회계/
    ├── 2023_2차_원가회계_원가회계+문제.pdf
    ├── 2024_2차_원가회계_원가회계+문제.hwp
    └── ...
```

실행 시 다음 옵션을 선택할 수 있습니다:
1. 모든 파일 다운로드
2. 1차 확정답안만 다운로드  
3. 특정 과목만 다운로드

#### 방법 3: process_03_v3_simple.py (고급 선택)
연도, 차수, 과목을 세밀하게 선택하여 다운로드할 수 있습니다.

**특징:**
- 연도별 선택 (특정 연도, 최근 5년, 최근 10년 등)
- 차수별 선택 (1차, 2차, 전체)
- 과목별 선택
- 확장자별 정리 옵션
- 실행 시간 기반 폴더명으로 충돌 방지

**저장 구조:**
```
download/
├── 20250111_143022_2024_2차_원가회계/
├── 20250111_144512_최근5년_1차/
├── 20250111_145023_2020-2024_전체/
└── ...
```

실행 시 대화형으로 다음을 선택할 수 있습니다:
- 연도 범위 (전체, 특정 연도, 최근 N년)
- 차수 (1차, 2차, 전체)
- 과목 (개별 선택 가능)
- 확정답안만 다운로드 여부 (1차만 해당)
- 확장자별 폴더 정리 여부

## 사용 순서

1. 먼저 게시물 URL을 수집합니다:
   ```bash
   python process_01_get_post_urls.py
   ```

2. 각 게시물에서 파일 URL을 추출합니다:
   ```bash
   python process_02_get_file_urls.py
   ```

3. 파일을 다운로드합니다 (셋 중 선택):
   - 기본 다운로드: `python process_03_downloadfiles.py`
   - 과목별 정리: `python process_03_v2_organized.py`
   - 고급 선택: `python process_03_v3_simple.py`

## 폴더 구조 예시

```
process-01-get-files/
├── process_01_get_post_urls.py
├── process_02_get_file_urls.py
├── process_03_downloadfiles.py
├── process_03_v2_organized.py
├── process_03_v3_simple.py
├── 01_post_urls_cache.csv        # 1단계 출력
├── 02_file_urls_cache.csv        # 2단계 출력
└── download/                      # 다운로드된 파일들
    ├── 20250111_143022_2차_원가회계/
    ├── 20250111_144512_1차_확정답안/
    └── ...
```

## 주의사항

- 네트워크 상태에 따라 다운로드 시간이 오래 걸릴 수 있습니다.
- 이미 다운로드된 파일은 자동으로 스킵됩니다.
- PDF와 HWP 파일이 혼재되어 있습니다.
- 모든 다운로드 파일은 `download/` 폴더 아래 저장됩니다.
# CPA 시험 자료 관리 시스템

금융감독원 공인회계사 시험 게시판에서 기출문제를 자동으로 수집하고 체계적으로 관리하는 도구

## 프로젝트 구조

```
cpa-exams/
├── tools/
│   ├── process-01-get-files/      # 시험 자료 수집 도구
│   │   ├── download/              # 다운로드 파일 저장 (gitignored)
│   │   ├── *_cache.csv            # URL 캐시 파일
│   │   └── process_*.py           # 수집 스크립트
│   │
│   ├── process-02-file-converter/ # 파일 형식 변환 도구
│   │   ├── using-llm/             # AI 기반 변환
│   │   ├── using-python/          # Python 기반 변환
│   │   └── using-claudecode/      # Claude Code 지원
│   │
│   └── process-solutions/         # 프로세스 설계 문서
│
├── _sessions/                     # 작업 세션 기록 (gitignored)
├── _temp/                         # 임시 파일
├── _assets/                       # 이미지, 리소스
└── docs/                          # 공개 문서
```

## 주요 기능

### 1. 자료 수집 (process-01-get-files)
- FSS 웹사이트에서 시험 자료 자동 다운로드
- 연도별, 차수별, 과목별 선택 다운로드 지원
- 타임스탬프 기반 폴더 자동 생성

### 2. 파일 변환 (process-02-file-converter)
- HWP/PDF → Markdown 변환
- AI 기반 변환 (Claude, Gemini API)
- Python 기반 변환 (개발 중)

### 3. 프로세스 설계 (process-solutions)
- 체계적인 문제 분석 워크플로우
- 프롬프트 템플릿 및 설계 문서


## 사용법

### 설치
```bash
pip install requests beautifulsoup4
```

### 전체 다운로드 프로세스
```bash
cd tools/process-01-get-files

# 1. 게시물 URL 수집
python process_01_get_post_urls.py

# 2. 파일 URL 추출
python process_02_get_file_urls.py

# 3. 대화형 다운로드
python process_03_v3_simple.py
```

### 특정 과목 다운로드
```bash
python process_03_v3_simple.py
# 2 선택 (선택 다운로드)
# 3 선택 (2차 시험만)
# 2 선택 (특정 과목)
# 4 입력 (원가회계)
```

## 기술적 세부사항

### 1. 자료 수집 프로세스

1. **게시물 URL 수집**: FSS 게시판에서 모든 게시물 목록 크롤링
2. **파일 URL 추출**: 각 게시물에서 첨부파일 URL 파싱
3. **파일 다운로드**: 선택한 조건에 따라 파일 다운로드

### 2. 파일 변환 프로세스

- **LLM 기반**: Claude/Gemini API를 통한 지능형 변환
- **Python 기반**: 프로그래밍 방식의 변환 (개발 중)
- **Claude Code 지원**: 대화형 변환 지원


---

원본 기출문제의 저작권은 금융감독원에게 있습니다.

All CPA exam questions are © FSS and may not be reproduced, distributed,
or publicly transmitted without prior written permission from FSS
(https://cpa.fss.or.kr).
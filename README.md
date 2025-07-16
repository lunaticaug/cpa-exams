# CPA 시험 데이터셋

`pdf`, `hwp` 형식으로 작성된 기출문제를 llm이 이용하기 좋은 filetype으로 변환합니다.

```
1. python을 이용한 웹크롤러;
2. 문서변환, OCR
3. 기출문제 분석 데이터
```

## 주요 기능

### 1. 자료 수집 (process-01-get-files)
수작업으로 처리하기 어려운 대량의 자료 일괄 다운로드, 
다양한 구조의 표가 포함되어있고 단편집 된 문서를 일관되게 
- FSS 웹사이트에서 시험 자료 자동 다운로드
- 연도별, 차수별, 과목별 선택 다운로드 지원
- 타임스탬프 기반 폴더 자동 생성

### 2. 파일 변환 (process-02-file-converter)
- HWP/PDF → Markdown 변환
- AI 기반 변환 (Claude, Gemini 웹)
- Python 라이브러리 이용

### 3. 프로세스 설계


## 프로젝트 구조

```
cpa-exams/
├── tools/
│   ├── process-01-get-files/      # 시험문제지 일괄 다운로드
│   │   └── process_*.py           # 수집 스크립트
│   │
│   ├── process-02-file-converter/ # 파일 형식 변환 도구
│   │   ├── using-llm/             # AI 기반 변환
│   │   ├── using-python/          # Python 기반 변환
│   │   └── using-claudecode/      # Claude Code 지원
│   │
│   └── process-solutions/         # 프로세스 설계 문서
│
├── _temp/                         # 임시 파일
└── _assets/                       # 이미지, 리소스
```


## 절차

### 1. 자료 수집 프로세스

1. **게시물 URL 수집**: FSS 게시판에서 모든 게시물 목록 크롤링
2. **파일 URL 추출**: 각 게시물에서 첨부파일 URL 파싱
3. **파일 다운로드**: 선택한 조건에 따라 파일 다운로드

### 2. 파일 변환 프로세스

- **LLM**: Claude/Gemini 웹 변환 프롬프트 모듈
- **Python**: RPA 자동화, 가장 기본적인 형태
- **Claude Code**: Vision + Python 혼합된 Agent 이용 (작업중)


---

원본 기출문제의 저작권은 금융감독원에게 있습니다.

All CPA exam questions are © FSS and may not be reproduced, distributed,
or publicly transmitted without prior written permission from FSS
(https://cpa.fss.or.kr).
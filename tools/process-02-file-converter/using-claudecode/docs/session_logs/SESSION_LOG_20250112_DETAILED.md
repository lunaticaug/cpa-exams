# 세션 로그 - 2025년 1월 12일

## 작업 개요
PDF to Markdown 변환 프로세스 개발 및 개선

## 수행한 작업

### 1. 초기 분석 및 파일 정리
- 원본 파일을 `source/` 폴더로 이동 (gitignore 적용)
- 파일명 규칙 적용: `process-XX-기능명.py`
- 출력 파일명 규칙: `output-XX-설명.json/md`

### 2. 변환 방법 탐색
1. **기본 PDF 변환** (process-03-pdf-to-markdown.py)
   - pdfplumber 사용
   - 문제점: 표 중복, 텍스트 순서 뒤섞임

2. **HWP 변환 경로 검토** (process-07-docx-conversion-test.py)
   - HWP → DOCX → Markdown 경로 제안
   - 2003-2015년 HWP 파일 13개는 별도 변환 필요

3. **개선된 PDF 변환** (process-08-improved-pdf-converter.py)
   - 표 처리 개선
   - 텍스트 구조화

### 3. 구조적 접근
1. **구조 분석기** (process-11-structure-analyzer.py)
   - 문제, 물음, 자료 등 계층 구조 추출
   - 42개 표를 가진 2024년 파일이 가장 복잡

2. **템플릿 기반 추출** (process-12/13)
   - 예상 구조를 JSON으로 정의
   - 템플릿 매칭 방식 시도

### 4. 레이아웃 인식 변환기 (최종)
**process-14-layout-aware-converter.py**
- 2단 레이아웃 자동 인식
- 컬럼 경계 감지 (x좌표 분석)
- 좌우 컬럼을 Y좌표 기준으로 올바른 순서로 병합

## 주요 발견사항

### 문제점
1. PDF의 2단 구성으로 인한 텍스트 뒤섞임
2. 표와 본문의 순서 혼재
3. 문장 중간에 "(물음 X)" 같은 패턴 삽입

### 해결 방법
- X 좌표 분석으로 컬럼 경계 자동 감지
- Y 좌표 기반 읽기 순서 복원
- 표 구조 개선 및 중복 제거

## 다음 세션에서 할 일

1. **HWP 파일 변환**
   - 2003-2015년 13개 HWP 파일을 DOCX로 변환
   - process-09-docx-to-markdown.py로 처리

2. **추가 개선사항**
   - 문장 병합 로직 개선 (끊어진 문장 연결)
   - 특수 패턴 후처리 규칙 추가

3. **일괄 처리**
   - 모든 연도 파일 최종 변환
   - 품질 검증

## 파일 구조
```
using-claudecode/
├── source/                          # 원본 파일 (gitignore)
├── output-14-layout-aware.md        # 최종 변환 결과
├── process-14-layout-aware-converter.py  # 최종 변환기
├── structure-template-2024.json     # 구조 템플릿
└── HWP_CONVERSION_GUIDE.md          # HWP 변환 가이드
```

## 기술 스택
- Python: pdfplumber, python-docx
- 필요 시: pandoc, mammoth

## 메모
- CLAUDE.md에 gitignore 파일 관리 지침 추가함
- 2024년 원가회계가 가장 복잡한 테스트 케이스
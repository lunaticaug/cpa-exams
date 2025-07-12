# using-claudecode

ClaudeCode를 활용한 PDF to Markdown 변환 도구

## 폴더 구조

```
using-claudecode/
├── _source/       # 원본 PDF/HWP 파일 (gitignore)
├── _archive/      # 이전 버전
├── output/        # 변환 결과 (버전별 관리)
│   └── VERSION_LOG.md
├── templates/     # 재사용 템플릿
│   └── structure/ # 구조 템플릿
├── workspace/     # 작업 중인 파일
│   └── VERSION_LOG.md
├── docs/          # 문서화
├── scripts/       # 실행 스크립트
└── log/           # 시스템 로그
```

## 버전 관리 규칙
- 모든 output은 v{major}.{minor} 형식 사용
- "final" 단어 사용 금지
- 설명은 VERSION_LOG.md에 기록

## 주요 스크립트

- `pdf_converter_v1.14.py` - 2단 레이아웃 PDF 변환기
- `structure_analyzer_v1.21.py` - 문서 구조 분석기
- `vision_based_template_v1.31.py` - Vision API 기반 구조 추출
- `efficient_pdf_processor_v1.30.py` - 효율적 PDF 처리 (캐싱)
- `batch_processor_v1.10.py` - 일괄 처리 도구
- `textbox_identifier_v1.25.py` - 텍스트박스 식별기

## 사용법

```bash
# PDF 변환
python pdf_converter_v1.14.py

# Vision API로 구조 추출
python vision_based_template_v1.31.py

# 일괄 처리
python batch_processor_v1.10.py
```

## 결과물 위치
- `sample/output_final_markdown/` - 2016-2025년 원가회계 변환 결과
- `sample/structure_templates/` - 연도별 구조 템플릿

## 주요 스크립트

### 메인 스크립트
- `batch_processor_v1.10.py` - 여러 파일 일괄 처리
- `pdf_converter_v1.14.py` - 2단 레이아웃 PDF 변환
- `structure_analyzer_v1.21.py` - 문서 구조 분석
- `textbox_identifier_v1.25.py` - 텍스트박스 식별
- `efficient_pdf_processor_v1.30.py` - 효율적 PDF 처리 (캐싱)
- `vision_based_template_v1.31.py` - Vision API 기반 구조 추출

### 개발 과정
1. `_archive/` - 초기 탐색 및 실험 (process-01~19)
2. `_draft/` - 정확도 개선 작업 (process-22~24)
3. 루트 레벨 - 최종 버전 스크립트

## 사용법

```bash
# PDF 변환
python pdf_converter_v1.14.py

# 구조 분석
python structure_analyzer_v1.21.py

# 일괄 처리
python batch_processor_v1.10.py
```

## 참고
- 원본 파일은 `_source/` 폴더에 저장 (git 추적 제외)
- 변환 결과는 `sample/` 폴더에 저장
- 개발 문서는 `_log/` 폴더 참조
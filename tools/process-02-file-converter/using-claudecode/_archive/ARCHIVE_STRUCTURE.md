# Archive 폴더 구조 및 명명 규칙

## 폴더 구조

```
_archive/
├── failed_scripts/           # 실패한 Python 스크립트들
│   ├── early_attempts/       # process-01~19 (초기 시도)
│   └── final_attempts/       # process-22~24 (최종 시도)
│
├── markdown-output/          # 실패한 변환 결과물들
│   └── x/                    # 실패작 모음
│       ├── converted_files/  # 버전별 변환 시도 (v1.00~v1.22)
│       ├── markdown/         # 초기 변환 결과
│       └── output_final_markdown2/  # 최종 정리본
│
└── 기타 실험 파일들
```

## 파일명 규칙 매핑

### Python 스크립트 → 출력 파일 매핑

| 스크립트 | 출력 폴더/파일 패턴 |
|---------|------------------|
| process-01~07 | 초기 분석 및 테스트 (출력 없음) |
| process-08 (improved_pdf_converter) | markdown_improved/ |
| process-09 (docx-to-markdown) | markdown_from_docx/ |
| process-11~19 | structured/ 폴더의 다양한 시도들 |
| pdf_converter_v1.14.py | markdown/ (초기 변환) |
| efficient_pdf_processor_v1.30.py | converted_files/연도_v1.XX_타임스탬프.md |
| batch_processor_v1.10.py | 배치 처리 (여러 파일 동시 변환) |

### 버전별 출력 특징

- **v1.00~v1.09**: 초기 버전, 기본 변환 시도
- **v1.10~v1.19**: 구조 인식 개선 시도
- **v1.20~v1.29**: 레이아웃 기반 접근
- **v1.30+**: 최종 개선 버전

## 실패 이유별 분류

### 1. 구조 인식 실패
- process-11~14: 템플릿 기반 접근 실패
- process-15~16: 단순 구조 채우기 실패

### 2. 내용 추출 실패
- process-17~18: 정확한 내용 추출 시도
- process-19: 수동 구조 채우기 시도

### 3. 순서 문제
- converted_files의 v1.00~v1.19: PDF 텍스트박스 순서 문제

## 최종 성공 버전

현재 workspace/scripts/에 있는 파일들:
- vision_based_template_v1.31.py
- efficient_pdf_processor_v1.30.py
- structure_analyzer_v1.21.py
- claude_vision_converter_v2.01.py

이들이 최종적으로 성공한 접근법입니다.
# 디렉토리 정리 계획

## 현재 상황
중첩된 디렉토리 구조로 인해 파일들이 3개 레벨에 분산되어 있음:
- Level 1: `/tools/process-02-file-converter/using-claudecode/`
- Level 2: `.../using-claudecode/tools/process-02-file-converter/using-claudecode/`
- Level 3: `.../using-claudecode/tools/.../using-claudecode/tools/.../using-claudecode/`

## 작업 순서

### 1단계: 파일 이동 계획
1. **Level 3의 파일을 Level 1로 이동**
   - `vision_based_template_v1.31.py` → `solution_v1.0/`

2. **Level 2의 파일을 Level 1로 이동**
   - `process-22-accurate-structure-extractor.py` → `solution_v1.0/`
   - `process-23-ordered-template-generator.py` → `solution_v1.0/`
   - `process-24-clean-structure-template.py` → `solution_v1.0/`
   - `textbox_identifier_v1.25.py` → `solution_v1.0/`
   - `efficient_pdf_processor_v1.30.py` → `solution_v1.0/`

### 2단계: 중복 파일 처리
- `SESSION_LOG_20250112_FINAL.md` - Level 3 버전 유지 (최신)
- 다른 중복 파일들은 Level 1 버전 유지

### 3단계: 빈 디렉토리 삭제
- 중첩된 `tools/` 디렉토리 구조 전체 삭제

### 4단계: 최종 구조
```
using-claudecode/
├── archive/                  # 초기 시도들 (process-01~19)
├── documentation/            # 프로젝트 문서
├── output/                   # 변환 결과물
├── solution_v1.0/           # 최종 솔루션 (v1.10~v1.31)
├── source/                  # 원본 파일 (HWP/PDF)
└── structure-templates/     # 구조 템플릿
```

## 버전별 개발 순서

### Phase 1: 초기 탐색 (process-01~09)
- PDF/HWP 구조 분석
- 기본 변환 시도
- DOCX 경유 방식 테스트

### Phase 2: 구조 분석 (process-11~13)
- 문서 구조 패턴 발견
- 템플릿 기반 접근법 개발
- 2단 레이아웃 문제 인식

### Phase 3: 실험적 접근 (process-15~19)
- 다양한 추출 방법 시도
- 수동 구조 채우기 실험

### Phase 4: 버전화 시작 (v1.10~v1.21)
- batch_processor_v1.10.py - 배치 처리
- pdf_converter_v1.14.py - 개선된 PDF 변환
- structure_analyzer_v1.21.py - 고급 구조 분석

### Phase 5: 정확도 개선 (process-22~24, v1.25)
- 정확한 구조 추출
- 깔끔한 템플릿 생성
- 텍스트박스 식별

### Phase 6: 최종 솔루션 (v1.30~v1.31)
- efficient_pdf_processor_v1.30.py - 효율적 처리
- vision_based_template_v1.31.py - Vision API 활용

## 다음 작업
1. 위 계획에 따라 파일 정리 실행
2. CLAUDE.md에서 중첩 디렉토리 경고 제거
3. 정리된 구조로 작업 계속 진행
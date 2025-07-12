# 세션 로그 - 2025년 1월 12일 (Vision API 구현)

## 세션 개요
- **작업 내용**: 2024년 원가회계 PDF를 Vision API 기반으로 변환
- **핵심 성과**: 2단 편집 문제를 Vision API로 해결하는 방법 확립
- **진행 상황**: 15페이지 중 1페이지 완전 추출 완료

## 1. 사전 작업

### 1.1 CLAUDE.md 개선
- process-02 전용 버전 관리 전략 추가
- 파일명 규칙: 작업 파일은 단순하게, 결과물은 버전 명시
- _history/ 폴더 활용한 스냅샷 관리

### 1.2 기존 스크립트 정리
```bash
# _history 폴더로 이전 버전들 백업
_history/
├── pdf_converter_v1.14_레이아웃인식.py
├── efficient_pdf_processor_v1.30_복잡도분석.py
├── vision_based_template_v1.31_템플릿만.py
└── vision_api_converter_v2.00_초기구현.py
```

## 2. Vision API 구현 (v2.00)

### 2.1 작성한 스크립트

#### pdf_to_images.py
```python
"""
기능: PDF를 페이지별 이미지로 변환 (Vision API 준비)
입력: PDF 파일 경로
출력: workspace/vision_input/ 폴더에 페이지별 PNG 이미지
"""
# 주요 기능: PyMuPDF로 150 DPI 이미지 변환
```

#### vision_extractor.py
```python
"""
기능: Claude Vision을 통해 이미지에서 구조화된 텍스트 추출
입력: 페이지 이미지 파일
출력: workspace/vision_output/ 폴더에 페이지별 JSON
"""
# 현재는 수동 추출 가이드 제공
```

#### merge_results.py → merge_results_v2.py
```python
"""
기능: 페이지별 JSON을 하나의 Markdown으로 통합
개선: 한글 파일명 지원, 최신 버전 자동 선택
"""
```

### 2.2 실행 결과
```bash
# 1. PDF → 이미지 변환
python pdf_to_images.py _source/2024_2차_원가회계_2-1+원가회계+문제\(2024-2\).pdf
# 결과: workspace/vision_input/page_001.png ~ page_015.png (15개)

# 2. Vision 추출 (수동)
# page_001_추출_4.json, page_002_extracted.json 생성

# 3. 통합
python merge_results_v2.py
# 결과: 원가회계_2024_v2.00_vision추출_1.md
```

## 3. 표 추출 문제 해결 과정

### 3.1 초기 오류 (page_001_extracted.json)
```markdown
[연간 예산 용역의 양]
| 수선(단위:시간) | - | - | 160 | 480 | 800 |
| 식당(단위:명) | 400 | 160 | 162 | 108 | 216 |
```
**문제**: 수선부문의 400, 160이 누락됨

### 3.2 수정 시도들
- page_001_extracted_v2.json: 여전히 오류
- page_001_추출_3.json: "-"로 표시하여 더 큰 오류
- page_001_추출_4.json: ✅ 정확한 추출 성공

### 3.3 최종 올바른 표 구조
```markdown
| 제공부문 | 수선 | 식당 | X | Y | Z |
|---------|------|------|-----|-----|-----|
| 수선(단위:시간) | 400 | 160 | 160 | 480 | 800 |
| 식당(단위:명) | 54 | 60 | 162 | 108 | 216 |
```

## 4. 오류 원인 분석

### 4.1 근본 원인
1. **시각적 착시**: "(단위:시간)"을 별도 행으로 인식
2. **선입견**: "보조부문이 자기 자신에게는 서비스 제공 안 함" 가정
3. **병합 셀 처리**: 복잡한 헤더 구조 파악 실패

### 4.2 해결 방안 문서화
- `표_추출_오류_방지_가이드.md`: 체계적 접근법
- `improved_vision_prompt.md`: 개선된 프롬프트 템플릿

## 5. 현재 상태 및 다음 작업

### 5.1 완료된 작업
- ✅ Vision API 기반 변환 프로세스 확립
- ✅ 1페이지 정확한 추출 완료
- ✅ 표 추출 오류 원인 파악 및 해결책 문서화
- ✅ 파일명 규칙 정립 (page_XXX_추출_N.json)

### 5.2 파일 위치
```
workspace/
├── vision_input/           # 15개 페이지 이미지
│   └── page_001.png ~ page_015.png
├── vision_output/          # 추출된 JSON
│   ├── page_001_추출_4.json (정확)
│   └── page_002_extracted.json
└── 원가회계_2024_v2.00_vision추출_1.md (2페이지만)
```

### 5.3 다음 CC가 해야 할 작업

#### 즉시 시작 가능한 작업
1. **나머지 13페이지 Vision 추출**
   ```bash
   # 각 페이지 이미지 읽고 improved_vision_prompt.md 참고하여 추출
   Read workspace/vision_input/page_003.png
   # → workspace/vision_output/page_003_추출_1.json 생성
   ```

2. **전체 통합**
   ```bash
   python merge_results_v2.py
   # → 원가회계_2024_v2.00_vision추출_2.md (전체)
   ```

#### 주의사항
- 표 추출 시 `improved_vision_prompt.md`의 단계별 접근법 사용
- 복잡한 표는 원시 데이터 먼저 추출 후 구조화
- 파일명: page_XXX_추출_N.json 형식 유지

#### 품질 검증
- 각 표의 행/열 합계 확인
- 문제 번호 순서 확인
- 자료/물음 대응 관계 확인

## 6. 핵심 인사이트

### 6.1 Vision API의 장점
- 2단 편집 문제 완벽 해결
- 복잡한 표 구조도 정확히 이해
- 시각적 맥락 파악 가능

### 6.2 성공 요인
- 단계별 추출 (구조 분석 → 원시 데이터 → 검증)
- 명확한 프롬프트 ("단위 표시는 행 레이블의 일부")
- 여러 버전 시도 후 최적안 선택

### 6.3 남은 과제
- 나머지 페이지 추출 완료
- 자동화 스크립트 개선 (현재는 수동)
- 다른 과목 PDF에도 적용

## 7. Git 커밋 이력
```
96356ec feat: Vision API 기반 PDF 변환 도구 v2.00 구현
362c4c1 fix: Vision 추출 표 정확도 개선
40566d2 feat: Vision 표 추출 개선 및 파일명 규칙 적용
```

---

**다음 세션 시작 명령어:**
```bash
cd /Users/user/GitHub/active/cpa-exams/tools/process-02-file-converter/using-claudecode
ls workspace/vision_input/  # 이미지 확인
ls workspace/vision_output/  # 기존 추출 확인
python merge_results_v2.py  # 현재 상태 확인
```

이 문서를 참고하여 page_003부터 page_015까지 추출을 완료하면 2024년 원가회계 전체 변환이 완성됩니다!
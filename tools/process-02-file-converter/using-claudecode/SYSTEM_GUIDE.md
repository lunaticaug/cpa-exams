# Vision API 오류 보완 통합 시스템 가이드

## 🎯 시스템 개요

Vision API로 PDF를 추출할 때 발생하는 오류(잘못된 숫자, 문자 혼동 등)를 보완하기 위한 다층적 검증 시스템입니다.

### 핵심 기능
1. **PDF Text Layer + Vision API 교차 검증**
2. **오류 패턴 자동 학습 및 수정**
3. **표 구조 자동 복원**
4. **신뢰도 기반 품질 관리**

## 🏗️ 시스템 구조

```
통합 PDF 처리 시스템
├── enhanced_pdf_processor.py      # 교차 검증 엔진
├── correction_learning_system.py  # 수정사항 학습 시스템
└── integrated_pdf_processor.py    # 통합 실행 모듈
```

## 🔄 작동 원리

### 1단계: 다중 소스 추출
```
PDF 파일 → PDF Text Layer 추출
       └→ Vision API 추출 (기존 JSON)
              ↓
         교차 검증 엔진
```

### 2단계: 교차 검증
- **Text Layer와 Vision API 결과 비교**
  - 일치율 95% 이상: Text Layer 신뢰 (신뢰도 98%)
  - 일치율 80-95%: 라인별 최적 선택 (신뢰도 85%)
  - 일치율 80% 미만: Vision API 우선 + 경고 (신뢰도 70%)

### 3단계: 자동 오류 수정
- **문자 혼동 패턴**: O↔0, l↔1, I↔1 등
- **숫자 형식**: 천단위 구분자, 소수점
- **특수문자**: 전각/반각 문자 정규화

### 4단계: 표 구조 복원
- 깨진 표 구조 자동 감지
- 열 개수 추정 및 파이프(|) 구분자 추가
- 정렬 및 포맷팅

## 📊 신뢰도 점수 체계

| 신뢰도 | 의미 | 조치 |
|--------|------|------|
| 90% 이상 | 높음 | 자동 승인 |
| 70-90% | 중간 | 검토 권장 |
| 70% 미만 | 낮음 | 수동 검토 필수 |

## 🚀 사용 방법

### 기본 사용법
```bash
# 통합 시스템 실행
python integrated_pdf_processor.py
```

### 개별 파일 처리
```python
from integrated_pdf_processor import IntegratedPDFProcessor

processor = IntegratedPDFProcessor()
processor.process_pdf_with_learning(
    pdf_path=Path("원가회계_2024.pdf"),
    output_path=Path("output/원가회계_2024_enhanced.md"),
    vision_dir=Path("__temp/2024/vision_output")
)
```

### 수정사항 학습
```python
from correction_learning_system import CorrectionLearningSystem

learner = CorrectionLearningSystem()
learner.learn_from_diff(
    original_file=Path("원본.md"),
    corrected_file=Path("수정본.md")
)
```

## 📈 검증 결과 예시

### 2024년 원가회계 검증 결과
- **Text Layer 품질**: 중간 (문자 수 500-1000)
- **Vision API와 불일치**: 40개 라인
- **자동 수정**: 17건
- **최종 신뢰도**: 85%

### 주요 오류 패턴
1. **표 구조 파괴**
   - 원인: Text Layer에서 표 구분자 누락
   - 해결: 자동 표 재구성 알고리즘

2. **숫자 인식 오류**
   - 원인: Vision API의 문자 혼동 (0과 O)
   - 해결: Text Layer 우선 + 패턴 검증

## 🔧 커스터마이징

### 오류 패턴 추가
```python
# enhanced_pdf_processor.py
self.error_patterns['custom'] = [
    (r'패턴', '교체값'),
]
```

### 신뢰도 가중치 조정
```python
CONFIDENCE_WEIGHTS = {
    'text_layer_match': 0.4,    # Text Layer 일치도
    'pattern_consistency': 0.3,  # 패턴 일관성
    'context_validation': 0.2,   # 컨텍스트 검증
    'format_compliance': 0.1     # 포맷 준수
}
```

## 📁 출력 파일

### 1. 향상된 추출 결과
```
integrated_output/
├── 파일명_integrated.md      # 최종 추출 결과
├── 파일명_integrated_report.json  # 처리 보고서
└── batch_processing_report.md     # 배치 처리 요약
```

### 2. 수정 이력
```
learned_corrections.json      # 학습된 수정 패턴
correction_learning_report.md # 학습 결과 보고서
```

## ⚠️ 주의사항

1. **PDF Text Layer 필수**
   - 스캔 PDF는 OCR 처리 후 사용
   - Text Layer 품질이 결과에 큰 영향

2. **Vision API 결과 필요**
   - 기존 Vision 추출 JSON 파일 필요
   - 없으면 Text Layer만으로 처리

3. **메모리 사용량**
   - 대용량 PDF는 페이지별 처리
   - 동시 처리 파일 수 제한 권장

## 🎯 개선 효과

### Before (Vision API만 사용)
- 문자 혼동 오류 다수
- 표 구조 파괴
- 수동 검토 필수

### After (통합 시스템)
- 오류 자동 감지 및 수정
- 표 구조 자동 복원
- 신뢰도 기반 품질 보증

## 📚 추가 개발 계획

1. **기계학습 기반 오류 예측**
2. **실시간 검증 대시보드**
3. **다국어 지원 확대**
4. **클라우드 배포 버전**

---

시스템 관련 문의나 개선 제안은 이슈로 등록해주세요!
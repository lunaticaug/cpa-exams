# Vision API 오류 보완 시스템 가이드

## 개요

Vision API 추출 결과의 정확도를 향상시키기 위한 통합 시스템입니다.
PDF의 Text Layer와 Vision API 결과를 교차 검증하고, 사용자의 수정사항을 학습하여 자동 적용합니다.

## 시스템 구성

### 1. 핵심 모듈

#### enhanced_pdf_processor.py
- PDF Text Layer 추출
- Vision API 결과와 교차 검증
- 신뢰도 점수 계산
- 오류 패턴 자동 수정

#### correction_learning_system.py
- 사용자 수정사항 학습
- 수정 패턴 추출 및 저장
- 학습된 패턴 자동 적용

#### integrated_pdf_processor.py
- 전체 시스템 통합
- 배치 처리
- 표 구조 개선
- 보고서 생성

### 2. 보조 도구

#### check_pdf_text_layer.py
- PDF Text Layer 품질 확인
- Text Layer 존재 여부 검사

#### validate_and_fix_extractions.py
- Vision API 결과 검증
- 불일치 항목 추출
- 검증 보고서 생성

## 사용 방법

### 1. 기본 사용법

```bash
# 통합 처리 실행
python integrated_pdf_processor.py

# 결과 확인
ls integrated_output/
```

### 2. 사용자 수정사항 학습

```bash
# 1. 원본과 수정본 준비
# sample/cost-accounting-2024.md (원본)
# sample/cost-accounting-2024_corrected.md (수정본)

# 2. 학습 실행
python correction_learning_system.py

# 3. 학습된 패턴 확인
cat learned_corrections.json
```

### 3. 개별 파일 처리

```python
from integrated_pdf_processor import IntegratedPDFProcessor

processor = IntegratedPDFProcessor()

# 단일 파일 처리
result = processor.process_pdf_with_learning(
    pdf_path=Path("your_pdf.pdf"),
    output_path=Path("output.md"),
    vision_dir=Path("vision_output/")
)

print(f"평균 신뢰도: {result['summary']['average_confidence']:.2%}")
```

## 시스템 특징

### 1. 교차 검증 방식

```
PDF Text Layer ─┐
                ├─→ Cross Validator ─→ Confidence Score ─→ Final Output
Vision API ─────┘
```

- Text Layer와 Vision API 결과가 95% 이상 일치: Text Layer 우선 (신뢰도 98%)
- 80-95% 일치: 라인별 최적 선택 (신뢰도 85%)
- 80% 미만 일치: Vision API 우선, Text Layer로 검증 (신뢰도 70%)

### 2. 자동 오류 수정

#### 문자 혼동 패턴
- 0 ↔ O (숫자 0과 알파벳 O)
- 1 ↔ l ↔ I (숫자 1, 소문자 l, 대문자 I)
- 5 ↔ S, 6 ↔ G, 8 ↔ B

#### 회계 숫자 형식
- 천단위 구분자 정규화
- 숫자 사이 공백 제거
- 원화 기호 정규화

#### 표 구조 복원
- 깨진 표 자동 감지
- 파이프 구분자 추가
- 열 정렬 개선

### 3. 학습 시스템

사용자가 수정한 내용을 자동으로 학습하여 유사한 오류를 자동 수정합니다.

```json
{
  "manual_corrections": [
    {
      "type": "table_structure",
      "pattern": "missing_pipe",
      "original": "구분 수선부문 식당부문",
      "corrected": "| 구분 | 수선부문 | 식당부문 |",
      "frequency": 15
    }
  ]
}
```

## 출력 형식

### 1. 메인 출력 (integrated.md)

```markdown
[페이지 1]
원가회계
2/16 1교시

| 구분 | 수선부문 | 식당부문 |
| 실제 변동원가 | 수선시간당 ￦47 | 1명당 ￦50 |
| 실제 고정원가 | ￦8,000 | ￦19,000 |

[extraction_confidence: 0.85]

---
```

### 2. 처리 보고서 (report.json)

```json
{
  "file": "원가회계_2024.pdf",
  "summary": {
    "total_pages": 15,
    "average_confidence": 0.85,
    "auto_corrections_applied": 42,
    "high_confidence_ratio": 0.73
  }
}
```

### 3. 배치 처리 보고서 (batch_processing_report.md)

| 파일명 | 페이지 수 | 평균 신뢰도 | 자동 수정 | 상태 |
|--------|-----------|------------|-----------|------|
| 2024_원가회계.pdf | 15 | 85.00% | 42 | ✅ |

## 권장사항

1. **Text Layer 품질 확인**
   - 처리 전 `check_pdf_text_layer.py` 실행
   - 고품질 Text Layer가 있으면 더 정확한 결과

2. **Vision API 결과 개선**
   - 복잡한 표는 고해상도로 재추출
   - 페이지별로 최적화된 프롬프트 사용

3. **지속적 개선**
   - 수정사항을 정기적으로 학습
   - 학습 데이터가 쌓일수록 정확도 향상

4. **신뢰도 기준**
   - 90% 이상: 자동 사용 가능
   - 70-90%: 간단한 검토 필요
   - 70% 미만: 상세 검토 필요

## 문제 해결

### Q: 표 구조가 계속 깨져 있습니다
A: `integrated_pdf_processor.py`의 `improve_table_structure()` 메서드를 수정하거나, 사용자가 수정한 표를 학습시켜주세요.

### Q: 특정 문자가 계속 잘못 인식됩니다
A: `enhanced_pdf_processor.py`의 `error_patterns`에 새로운 패턴을 추가하세요.

### Q: 학습이 제대로 되지 않습니다
A: `learned_corrections.json`을 확인하고, 수정 전/후가 명확히 구분되는지 확인하세요.

## 다음 단계

1. 더 많은 PDF 파일로 테스트
2. 수정사항 지속적 학습
3. 표 구조 인식 알고리즘 개선
4. 도메인별 특화 규칙 추가 (회계, 법률 등)

---

이 시스템은 지속적으로 개선되고 있습니다. 
문제나 개선사항이 있으면 피드백 부탁드립니다.
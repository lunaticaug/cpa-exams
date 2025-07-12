# 다음 작업자를 위한 즉시 실행 가이드

## 🚀 빠른 시작

### 1. 현재 위치로 이동
```bash
cd /Users/user/GitHub/active/cpa-exams/tools/process-02-file-converter/using-claudecode
```

### 2. 현재 상태 확인
```bash
# 이미지 확인 (15개 있어야 함)
ls workspace/vision_input/*.png | wc -l

# 기존 추출 확인 (현재 2개)
ls workspace/vision_output/*.json

# 현재 통합 결과 확인
cat 원가회계_2024_v2.00_vision추출_1.md | head -20
```

## 📝 핵심 작업: 페이지 3~15 추출

### 예시: 3페이지 추출
```
1. Read workspace/vision_input/page_003.png

2. 다음 프롬프트 사용:
"""
이미지의 표를 추출합니다. 단계별 접근:

1단계: 표 구조 분석
- 전체 행/열 개수 확인
- 병합된 셀 위치 파악
- 헤더 구조 이해

2단계: 원시 데이터 추출
- 각 셀의 정확한 내용을 위치와 함께 기록
- 빈 셀도 명시적으로 표시
- "(단위:XX)"는 행 레이블의 일부임을 명심

3단계: 검증
- 행별 데이터 개수 = 열 개수
- 숫자 위치의 논리성 확인

JSON 형식으로 반환:
{
  "page_number": 3,
  "content": "마크다운 형식의 추출 내용",
  "problems": [...],
  "extraction_notes": "특이사항"
}
"""

3. 결과를 workspace/vision_output/page_003_추출_1.json으로 저장
```

### 전체 통합
```bash
# 모든 페이지 추출 완료 후
python merge_results_v2.py
# → 원가회계_2024_v2.00_vision추출_2.md 생성
```

## ⚠️ 주의사항

### 표 추출 시
- **함정 1**: "(단위:시간)"을 별도 행으로 착각 → 행 레이블의 일부
- **함정 2**: 빈 첫 열 → 데이터가 없는 게 아니라 다음 열에 있을 수 있음
- **함정 3**: 상호배분 → 보조부문이 자기 자신에게도 서비스 제공 가능

### 파일명 규칙
- 추출 파일: `page_XXX_추출_N.json`
- 수정 시: N을 증가 (추출_1 → 추출_2)
- 통합 결과: `원가회계_2024_v2.00_vision추출_N.md`

## 📊 진행 상황 추적

| 페이지 | 상태 | 파일명 | 비고 |
|--------|------|---------|------|
| 1 | ✅ 완료 | page_001_추출_4.json | 표 정확 |
| 2 | ✅ 완료 | page_002_extracted.json | |
| 3-15 | ⏳ 대기 | | 추출 필요 |

## 🔧 문제 발생 시

### 표가 복잡한 경우
1. `improved_vision_prompt.md` 참고
2. 원시 데이터 먼저 추출
3. 수동으로 구조 재구성

### 이미지가 안 보이는 경우
```bash
# 이미지 확인
file workspace/vision_input/page_XXX.png
# PNG image data, 1240 x 1754 같은 정보 나와야 함
```

## 💡 팁

1. **일괄 처리보다 정확도 우선**
   - 한 페이지씩 확인하며 진행
   - 특히 표가 있는 페이지는 신중히

2. **커밋 자주 하기**
   - 5페이지마다 중간 커밋
   - 파일명: "feat: 페이지 X-Y Vision 추출 완료"

3. **검증 습관**
   - 추출 후 원본 이미지와 대조
   - 특히 숫자와 표 구조 확인

---

**성공적인 작업을 위한 체크리스트:**
- [ ] workspace/vision_input/ 이미지 15개 확인
- [ ] improved_vision_prompt.md 읽기
- [ ] page_003부터 순차 추출
- [ ] 5페이지마다 merge_results_v2.py 실행하여 중간 점검
- [ ] 전체 완료 후 최종 통합

화이팅! 🎯
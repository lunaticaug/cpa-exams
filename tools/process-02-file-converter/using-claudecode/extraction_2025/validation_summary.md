# 2025년 원가관리회계 추출 검증 보고서
생성일시: 2025-07-13 01:44:27

## 발견된 오류

### 텍스트 오류 (9건)
- **직입노무원가** → 직접노무원가
  - 컨텍스트: ...,463단위 | ? |  | 구분 | 직접재료원가 | 직입노무원가 | 제조간접원가 | |------|----------...
- **평작업이라는 대한 코스트** → 재작업에 대한
  - 컨텍스트: ...량 투입되며, 전환원가는 공정 전반에 걸쳐 발생한다. 평작업이라는 대한 코스트 공정의 50% 시점에서 실시되며, 불량품은 공정의 1...
- **공손 이루어 대한** → 공손에 대한
  - 컨텍스트: ... 합격한 물량의 2.5%는 정상적인 것으로 간주한다. 공손 이루어 대한 검사는 공정의 80%에서 이루어진다. 검사한 물량의 ...
- **8,463** → 8,460
  - 컨텍스트: ... 당기완성 | 3,000단위 | | | 기말재공품 | 8,463단위 | ? |  | 구분 | 직접재료원가 | 직입노무...
- **평작업이라는 대한 코스트** → 재작업에 대한
  - 컨텍스트: ...량 투입되며, 전환원가는 공정 전반에 걸쳐 발생한다. 평작업이라는 대한 코스트 공정의 50% 시점에서 실시되며, 불량품은 공정의 1...

### 숫자 불일치
- Vision에만 있는 숫자: 120,000, 3,000, 8,463
- Vision에만 있는 숫자: 120,000, 3,000, 8,463
- Vision에만 있는 숫자: 120,000, 3,460, 3,000

## 권장사항
1. '직입노무원가' → '직접노무원가' 수정 필요
2. 의심스러운 숫자(8,463) 재확인 필요
3. 문맥상 이상한 표현 수정 필요

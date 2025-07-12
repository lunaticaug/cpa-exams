# CLAUDE.md - CPA Exams Project Guidelines

This file provides PROJECT-SPECIFIC guidance to Claude Code for the CPA Exams project.
**This overrides any conflicting guidelines in the global CLAUDE.md.**

## 1. 프로젝트 개요

### 1.1 목적
금융감독원 공인회계사 시험 게시판에서 기출문제를 자동으로 수집하고 체계적으로 관리하는 도구 개발
사용자의 목적에 맞게 적절한 대응방안을 설계하고 수행하세요. 
deep think 모드로 계획하고 최적의 결과물을 위한 작업을 수행합니다.
의도와 목적을 파악하세요.

### 1.2 작업 원칙
파일경로, 파일명명규칙을 제외하고는 클로드의 자율적인 판단에 따라 작업을 수행할 수 있습니다.
deep think를 이용하여 사용자의 의도와 목표를 이해하고, 그에 맞는 전략을 수립하세요.
gitignore에 등록된 추적 제외 파일/폴더는 사용자가 특별한 의도로 관리하는 것이므로 신중하게 다루어야 합니다.

## 2. 프로젝트 구조

프로젝트 구조는 README.md를 참조하세요. 

### 🚨 필수 경로 참조 원칙

**모든 파일 작업 시 반드시 다음을 준수하세요:**

1. **현재 위치 확인**
   - 작업 시작 시 `pwd` 명령으로 현재 위치 확인
   - 기본 작업 디렉토리: 프로젝트 루트 (cpa-exams/)
   - 하위 폴더로 이동했다면 작업 완료 후 원위치로 복귀

2. **절대 경로 사용**
   - 파일 읽기/쓰기 시 절대 경로 사용 권장
   - 상대 경로 사용 시 현재 위치 기준임을 명확히 인지

3. **경로 검증**
   - 파일 생성 전: 대상 폴더 존재 여부 확인 (`LS` 도구 사용)
   - 파일 이동 시: 출발지와 목적지 경로 모두 확인
   - 잘못된 위치에 파일 생성 시 즉시 올바른 위치로 이동

4. **프로세스별 경로 규칙**
   ```
   process-01 관련 → tools/process-01-get-files/
   process-02 관련 → tools/process-02-file-converter/
   전체 프로젝트 → 루트 또는 /docs/
   ```

### 주요 폴더별 작업 가이드

**tools/process-01-get-files/**
- 모든 다운로드는 `download/` 하위에 타임스탬프 폴더로 저장
- 캐시 파일(*_cache.csv)을 활용하여 중복 작업 방지

**tools/process-02-file-converter/**
- 각 변환 방식별로 독립적인 하위 폴더 관리
- 변환 결과는 각 방식의 하위 폴더에 저장
- `using-claudecode/` 폴더 구조:
  - `_archive/` - 초기 시도 및 실험 스크립트 (process-01~19)
  - `workspace/` - 현재 작업 중인 활성 코드
    - `scripts/` - 최종 버전 스크립트 (v1.10~v1.31)
    - `structure/` - 구조 분석 결과
  - `_source/` - 원본 HWP/PDF 파일
  - `docs/` - process-02 전용 문서 (세션 로그, 기술 문서)

**tools/process-solutions/**
- 프롬프트 템플릿과 설계 문서 참고

## 3. 파일 저장 규칙

### 3.1 다운로드 경로 구조
모든 다운로드 파일은 실행 시간 기반으로 고유한 폴더에 저장됩니다:
- 기본 경로: `tools/process-01-get-files/download/`
- 폴더명 형식: `{YYYYMMDD_HHMMSS}_{조건설명}/`
- 예시:
  - `download/20250111_143022_2차_원가회계/`
  - `download/20250111_144512_최근5년_1차/`
  - `download/20250111_145023_전체/`

### 3.2 파일명 규칙
다운로드된 파일은 다음 형식으로 저장됩니다:
- 형식: `{연도}_{차수}_{과목}_{원본파일명}.{확장자}`
- 예시: `2024_2차_원가회계_원가관리회계+문제.pdf`

### 3.3 확장자별 정리 (선택사항)
사용자 선택 시 확장자별 하위 폴더를 생성할 수 있습니다:
```
download/20250111_143022_2차_원가회계/
├── pdf/
│   └── 2024_2차_원가회계_문제.pdf
└── hwp/
    └── 2024_2차_원가회계_문제.hwp
```

### 3.4 gitignore 설정
- `**/download/**`로 설정되어 모든 다운로드 파일은 git에서 자동 제외됩니다
- 캐시 파일들도 `*_cache*` 규칙에 의해 제외됩니다

## 4. 파일명 규칙

### 4.1 기본 원칙
- 간결하고 직관적인 이름 사용
- 순차 실행 스크립트: `process_{순번}_{기능}.py`
- 기능 변형: `_v2`, `_v3` 등으로 구분
- 동일한 파일의 수정은 일반적인 버전 명명규칙을 따름 1.0.0. major, minor etcs

### 4.2 파일 상단 주석
모든 Python 파일은 상단에 다음 형식의 주석 포함:
```python
"""
기능: [간단한 설명]
입력: [필요한 입력 파일/데이터]
출력: [생성되는 파일/폴더]
"""
```

### 4.3 명명 예시
- `process_01_get_posts.py` - 게시물 URL 수집
- `process_03_download.py` - 기본 다운로드
- `process_03_download_v2.py` - 기능 확장 버전

### 4.4 process-02 버전 관리 전략

process-02는 반복 실험을 통한 최적화가 목적이므로 특별한 버전 관리 전략을 사용합니다:

#### 작업 파일 관리
1. **메인 작업 파일은 단순한 이름 유지**
   - 예: `pdf_converter.py`, `structure_analyzer.py`
   - Git이 변경 이력을 추적하도록 함
   - 파일명을 변경하지 않아 이력 연속성 보장

2. **_history/ 폴더에 버전별 스냅샷 보관**
   - 중요한 개발 시점마다 백업
   - 형식: `{파일명}_v{버전}_{설명}.py`
   - 예: `pdf_converter_v1.00_기본추출.py`
   - 예: `pdf_converter_v2.00_vision구현.py`

3. **결과물은 버전 정보 명시**
   - 형식: `{과목}_{연도}_v{버전}_{설명}.{ext}`
   - 예: `원가회계_2024_v1.00_기본추출.md`
   - 예: `원가회계_2024_v2.00_vision결과.md`
   - 어떤 버전의 스크립트로 생성했는지 추적 가능

#### 폴더 구조 예시
```
using-claudecode/
├── pdf_converter.py              # 현재 작업 중 (Git 추적)
├── _history/                     # 버전별 스냅샷
│   ├── pdf_converter_v1.00_기본추출.py
│   └── pdf_converter_v2.00_vision구현.py
└── workspace/output/             # 결과물
    ├── 원가회계_2024_v1.00_기본추출.md
    └── 원가회계_2024_v2.00_vision결과.md
```

이 방식으로 Git 이력을 보존하면서도 각 접근법의 결과를 비교할 수 있습니다.

## 5. 과목 분류 체계

### 5.1 1차 시험 과목
- 경영학 (경영학)
- 경제학 (경제원론, 경제학)
- 상법 (상법)
- 세법 (세법개론, 세법)
- 회계학 (회계학)
- 영어 (영어)
- 답안 (답안, 정답, 가답안, 확정답안, 확정정답, 최종정답)

### 5.2 2차 시험 과목
- 세법 (세법)
- 재무관리 (재무관리)
- 회계감사 (회계감사)
- 원가회계 (원가회계, 원가관리회계)
- 재무회계 (재무회계)

### 5.3 확정답안 판별 규칙
- 확정답안 키워드: "확정", "최종", "(최종)", "(확정)"
- 가답안 키워드: "가답안"
- 확정답안은 1차 시험에만 제공됨

## 6. 캐시 파일 관리

- `post_urls_cache.csv`: 게시물 URL 캐시
- `file_urls_cache.csv`: 파일 URL 캐시
- 캐시 갱신: 파일 삭제 후 재실행

사용법 및 명령어는 README.md를 참조하세요.

## 7. Git 커밋 및 브랜치 전략

### 7.1 브랜치 전략
작업의 성격에 따라 다른 브랜치 전략을 사용합니다:

**Main 브랜치에 직접 커밋하는 경우:**
- ✅ 사용자가 명시적으로 승인한 작업만 해당

**별도 브랜치 생성 + PR이 필요한 경우:**
- ⚠️ 파일 삭제
- ⚠️ 대규모 리팩토링
- ⚠️ 주요 기능 변경
- ⚠️ 디렉토리 구조 변경
- ⚠️ 설정 파일 수정 (.gitignore, config 등)
- ⚠️ 외부 의존성 추가/변경
- 📝 문서 개선 (README.md, CLAUDE.md 등)
- 🐛 버그 수정이나 개선사항
- 💬 오타 수정, 주석 추가
- 🧪 테스트 추가, 리팩토링

### 7.2 커밋 메시지 규칙
```
타입: 제목 (50자 이내)

- 변경사항 1
- 변경사항 2

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**커밋 타입:**
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅, 세미콜론 누락 등
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가
- `chore`: 빌드 작업, 패키지 관리자 설정 등

### 7.3 브랜치 명명 규칙
- 기능 추가: `feature/기능명`
- 버그 수정: `fix/이슈명`
- 문서 작업: `docs/문서명`
- 리팩토링: `refactor/대상`

## 8. 세션 문서화

### 8.1 폴더 구조
```
├── _sessions/                # Claude와의 작업 기록 (gitignore)
│   ├── active/               # 현재 진행 중
│   ├── completed/            # 완료된 세션
│   └── questions/            # 재사용 가능한 질문 템플릿
│
└── docs/                     # 외부 공개용 문서
    └── guides/               # 정리된 가이드 문서
```

### 8.2 파일명 규칙
- 세션 파일: `YYYYMMDD_주제.md`
- 질문 템플릿: `category_topic.md`
- 주제는 영문, 언더스코어로 단어 구분

---

## 9. 일반적인 작업 명령어

### 9.1 파일 변환 작업
```bash
# PDF 변환 작업 실행
cd tools/process-02-file-converter/using-claudecode/
python pdf_converter_v1.14.py

# 구조 분석 실행
python structure_analyzer_v1.21.py

# 배치 처리 실행
python batch_processor_v1.10.py
```

### 9.2 문서 저장 위치 규칙

**문서 종류별 저장 위치:**
```
전체 프로젝트 문서 → /docs/
process-01 문서 → /tools/process-01-get-files/docs/
process-02 문서 → /tools/process-02-file-converter/docs/
작업 세션 기록 → /_sessions/
실험/실패 기록 → 각 process의 _archive/
```

**⚠️ 주의사항:**
- process-01(다운로드) 관련 내용을 process-02 폴더에 저장하지 말 것
- 새 문서 작성 시 먼저 어느 process에 속하는지 확인
- 불확실한 경우 사용자에게 확인 요청

### 9.3 캐시 재생성
```bash
# 게시물 URL 캐시 삭제 및 재수집
rm tools/process-01-get-files/post_urls_cache.csv
python tools/process-01-get-files/process_01_get_posts.py

# 파일 URL 캐시 삭제 및 재수집
rm tools/process-01-get-files/file_urls_cache.csv
python tools/process-01-get-files/process_02_get_file_urls.py
```

### 9.3 다운로드 실행
```bash
# 기본 다운로드
python tools/process-01-get-files/process_03_download.py

# 조건부 다운로드 (대화형)
python tools/process-01-get-files/process_03_download_v2.py
```

---

이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.
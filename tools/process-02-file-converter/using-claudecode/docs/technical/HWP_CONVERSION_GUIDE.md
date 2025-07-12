
# HWP → DOCX → Markdown 변환 가이드

## 1단계: HWP → DOCX 변환

### 방법 1: 한컴오피스 사용 (권장)
1. 한컴오피스에서 HWP 파일 열기
2. 파일 → 다른 이름으로 저장
3. 파일 형식: Microsoft Word 문서 (*.docx)
4. 저장

### 방법 2: 온라인 변환 도구
- CloudConvert: https://cloudconvert.com/hwp-to-docx
- Zamzar: https://www.zamzar.com/convert/hwp-to-docx/
- Convertio: https://convertio.co/kr/hwp-docx/

### 방법 3: LibreOffice (부분 지원)
```bash
soffice --headless --convert-to docx *.hwp
```

## 2단계: DOCX → Markdown 변환

### 자동 변환
```bash
python process-09-docx-to-markdown.py
```

### Pandoc 사용 (설치 필요)
```bash
pandoc input.docx -o output.md --extract-media=media
```

## 주의사항
- 복잡한 수식은 이미지로 변환될 수 있음
- 표 구조가 단순화될 수 있음
- 변환 후 검토 필요

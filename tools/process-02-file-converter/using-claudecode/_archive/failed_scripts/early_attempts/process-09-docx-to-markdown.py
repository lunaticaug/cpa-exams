"""
기능: DOCX to Markdown 변환기
입력: DOCX 파일
출력: 구조화된 Markdown 파일
"""

from pathlib import Path
import re
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

class DocxToMarkdownConverter:
    def __init__(self):
        self.content = []
        self.table_counter = 0
        
    def convert_table(self, table):
        """DOCX 표를 Markdown으로 변환"""
        self.table_counter += 1
        
        if not table.rows:
            return ""
        
        markdown_lines = []
        
        # 헤더 행
        header_cells = []
        for cell in table.rows[0].cells:
            header_cells.append(cell.text.strip())
        
        markdown_lines.append("| " + " | ".join(header_cells) + " |")
        markdown_lines.append("|" + "|".join([" --- " for _ in header_cells]) + "|")
        
        # 데이터 행
        for row in table.rows[1:]:
            row_cells = []
            for cell in row.cells:
                row_cells.append(cell.text.strip())
            markdown_lines.append("| " + " | ".join(row_cells) + " |")
        
        return "\n".join(markdown_lines)
    
    def process_paragraph(self, para):
        """단락 처리 및 포맷팅"""
        text = para.text.strip()
        if not text:
            return ""
        
        # 문제 번호 패턴
        text = re.sub(r'【문제\s*(\d+)】\s*\((\d+)점\)', r'\n## 문제 \1 (\2점)\n', text)
        
        # 물음 번호
        text = re.sub(r'\(물음\s*(\d+)\)', r'\n### (물음 \1)\n', text)
        
        # 자료 표시
        text = re.sub(r'<자료\s*(\d+)>', r'\n#### <자료 \1>\n', text)
        
        # 답안양식
        text = re.sub(r'\(답안양식\)', r'\n**[답안양식]**\n', text)
        
        # 굵은 글씨 처리 (if runs have bold)
        if any(run.bold for run in para.runs):
            text = f"**{text}**"
        
        return text
    
    def convert_docx(self, docx_path, output_path):
        """DOCX 파일을 Markdown으로 변환"""
        print(f"변환 중: {docx_path.name}")
        
        # 초기화
        self.content = []
        self.table_counter = 0
        
        # 문서 열기
        doc = Document(docx_path)
        
        # 메타데이터
        year = docx_path.stem.split('_')[0] if '_' in docx_path.stem else "20XX"
        self.content.append(f"# {year}년 2차 원가회계 기출문제\n")
        self.content.append(f"> 원본 파일: {docx_path.name}\n")
        self.content.append(f"> 변환 경로: HWP → DOCX → Markdown\n")
        
        # 문서 요소 순회
        for element in doc.element.body:
            if element.tag.endswith('p'):  # 단락
                para = Paragraph(element, doc)
                text = self.process_paragraph(para)
                if text:
                    self.content.append(text)
            
            elif element.tag.endswith('tbl'):  # 표
                table = Table(element, doc)
                self.content.append("\n")
                self.content.append(self.convert_table(table))
                self.content.append("\n")
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.content))
        
        print(f"  ✓ 완료: {output_path.name}")
        return True

def create_conversion_guide():
    """HWP → DOCX 변환 가이드 생성"""
    guide = """
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
"""
    
    with open("HWP_CONVERSION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("변환 가이드가 HWP_CONVERSION_GUIDE.md에 저장되었습니다.")

def main():
    # 변환 가이드 생성
    create_conversion_guide()
    
    # DOCX 파일이 있다면 테스트
    docx_files = list(Path("source").glob("*.docx"))
    
    if docx_files:
        converter = DocxToMarkdownConverter()
        output_dir = Path("output/markdown_from_docx")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for docx_file in docx_files[:1]:  # 첫 번째 파일만 테스트
            output_file = output_dir / f"{docx_file.stem}.md"
            converter.convert_docx(docx_file, output_file)
    else:
        print("\nDOCX 파일이 없습니다.")
        print("HWP 파일을 먼저 DOCX로 변환해주세요.")
        print("변환 가이드: HWP_CONVERSION_GUIDE.md 참조")

if __name__ == "__main__":
    main()
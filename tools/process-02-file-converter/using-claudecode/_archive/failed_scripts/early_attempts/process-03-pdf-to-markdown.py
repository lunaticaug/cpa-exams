"""
기능: PDF를 Markdown으로 변환 (하이브리드 방식)
입력: PDF 파일
출력: Markdown 파일
"""

import pdfplumber
import fitz
from pathlib import Path
import re

class PDFToMarkdownConverter:
    def __init__(self):
        self.content = []
        
    def convert_table_to_markdown(self, table):
        """표를 Markdown 테이블로 변환"""
        if not table or not table[0]:
            return ""
        
        markdown_table = []
        
        # 헤더 행
        header = [cell if cell else "" for cell in table[0]]
        markdown_table.append("| " + " | ".join(header) + " |")
        
        # 구분선
        separator = "|"
        for _ in header:
            separator += " --- |"
        markdown_table.append(separator)
        
        # 데이터 행
        for row in table[1:]:
            cleaned_row = [cell if cell else "" for cell in row]
            markdown_table.append("| " + " | ".join(cleaned_row) + " |")
        
        return "\n".join(markdown_table)
    
    def extract_questions(self, text):
        """문제 번호와 배점을 추출하고 포맷팅"""
        # 【문제 N】(X점) 패턴 찾기
        pattern = r'【문제\s*(\d+)】\s*\((\d+)점\)'
        
        def replace_question(match):
            num = match.group(1)
            points = match.group(2)
            return f"\n## 문제 {num} ({points}점)\n"
        
        return re.sub(pattern, replace_question, text)
    
    def extract_sub_questions(self, text):
        """하위 문제 (물음 N) 패턴 처리"""
        pattern = r'\(물음\s*(\d+)\)'
        
        def replace_sub_question(match):
            num = match.group(1)
            return f"\n### (물음 {num})"
        
        return re.sub(pattern, replace_sub_question, text)
    
    def process_page(self, page, page_num):
        """페이지 처리"""
        self.content.append(f"\n---\n\n# 페이지 {page_num}\n")
        
        # 텍스트 추출
        text = page.extract_text()
        if text:
            # 문제 번호 포맷팅
            text = self.extract_questions(text)
            text = self.extract_sub_questions(text)
            
            # 텍스트를 줄 단위로 분리
            lines = text.split('\n')
            
            # 표 추출
            tables = page.extract_tables()
            table_positions = []
            
            # 표의 대략적인 위치를 찾기 위해 표의 첫 번째 셀 내용 저장
            for table in tables:
                if table and table[0] and table[0][0]:
                    first_cell = str(table[0][0]).strip()
                    if first_cell:
                        table_positions.append(first_cell)
            
            # 텍스트 처리
            current_text = []
            table_index = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 표의 시작점인지 확인
                if table_index < len(table_positions) and line.startswith(table_positions[table_index]):
                    # 현재까지의 텍스트 추가
                    if current_text:
                        self.content.append('\n'.join(current_text))
                        current_text = []
                    
                    # 표 추가
                    self.content.append("\n")
                    self.content.append(self.convert_table_to_markdown(tables[table_index]))
                    self.content.append("\n")
                    table_index += 1
                else:
                    current_text.append(line)
            
            # 남은 텍스트 추가
            if current_text:
                self.content.append('\n'.join(current_text))
            
            # 처리되지 않은 표가 있다면 페이지 끝에 추가
            while table_index < len(tables):
                self.content.append("\n")
                self.content.append(self.convert_table_to_markdown(tables[table_index]))
                self.content.append("\n")
                table_index += 1
    
    def convert_pdf(self, pdf_path, output_path):
        """PDF 파일을 Markdown으로 변환"""
        self.content = []
        
        # 제목 추가
        filename = pdf_path.stem
        year = filename.split('_')[0]
        subject = filename.split('_')[3] if len(filename.split('_')) > 3 else "원가회계"
        
        self.content.append(f"# {year}년 2차 {subject} 기출문제\n")
        self.content.append(f"\n파일명: {pdf_path.name}\n")
        
        # PDF 처리
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                self.process_page(page, i + 1)
        
        # Markdown 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.content))
        
        return output_path

def main():
    # 테스트: 2024년 파일 변환
    converter = PDFToMarkdownConverter()
    
    source_file = Path("source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    output_dir = Path("output/markdown")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{source_file.stem}.md"
    
    print(f"변환 중: {source_file.name}")
    converter.convert_pdf(source_file, output_file)
    print(f"완료: {output_file}")
    
    # 결과 미리보기
    with open(output_file, 'r', encoding='utf-8') as f:
        preview = f.read()[:1000]
        print("\n--- 변환 결과 미리보기 ---")
        print(preview)
        print("...")

if __name__ == "__main__":
    main()
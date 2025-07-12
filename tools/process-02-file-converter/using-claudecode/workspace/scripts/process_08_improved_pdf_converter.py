"""
기능: 개선된 PDF to Markdown 변환 (표 처리 강화)
입력: PDF 파일
출력: 구조화된 Markdown 파일
"""

import pdfplumber
from pathlib import Path
import re
import json

class ImprovedPDFConverter:
    def __init__(self):
        self.content = []
        self.table_counter = 0
        
    def clean_cell(self, cell):
        """셀 내용 정리"""
        if cell is None:
            return ""
        return str(cell).strip().replace('\n', ' ')
    
    def is_valid_table(self, table):
        """유효한 표인지 확인"""
        if not table or len(table) < 2:
            return False
        # 최소 2개 이상의 비어있지 않은 셀이 있는지 확인
        non_empty_cells = sum(1 for row in table for cell in row if cell and str(cell).strip())
        return non_empty_cells >= 2
    
    def convert_table_to_markdown(self, table):
        """표를 Markdown으로 변환 (개선된 버전)"""
        if not self.is_valid_table(table):
            return ""
        
        # 표 번호 증가
        self.table_counter += 1
        
        # 빈 행 제거
        cleaned_table = []
        for row in table:
            cleaned_row = [self.clean_cell(cell) for cell in row]
            if any(cell for cell in cleaned_row):  # 최소 하나의 셀에 내용이 있으면
                cleaned_table.append(cleaned_row)
        
        if not cleaned_table:
            return ""
        
        # 열 수 맞추기 (가장 많은 열을 기준으로)
        max_cols = max(len(row) for row in cleaned_table)
        for row in cleaned_table:
            while len(row) < max_cols:
                row.append("")
        
        # Markdown 표 생성
        markdown_lines = []
        
        # 헤더
        header = cleaned_table[0]
        markdown_lines.append("| " + " | ".join(header) + " |")
        
        # 구분선
        markdown_lines.append("|" + "|".join([" --- " for _ in header]) + "|")
        
        # 데이터 행
        for row in cleaned_table[1:]:
            markdown_lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(markdown_lines)
    
    def extract_text_with_structure(self, page):
        """페이지에서 구조화된 텍스트 추출"""
        # 페이지 전체 텍스트
        full_text = page.extract_text()
        if not full_text:
            return "", []
        
        # 표 추출
        tables = page.extract_tables()
        valid_tables = []
        
        # 유효한 표만 필터링
        for table in tables:
            if self.is_valid_table(table):
                valid_tables.append(table)
        
        return full_text, valid_tables
    
    def process_text(self, text):
        """텍스트 전처리 및 구조화"""
        # 불필요한 공백 정리
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 문제 번호 강조
        text = re.sub(r'【문제\s*(\d+)】\s*\((\d+)점\)', r'\n## 문제 \1 (\2점)\n', text)
        
        # 물음 번호
        text = re.sub(r'\(물음\s*(\d+)\)', r'\n### (물음 \1)\n', text)
        
        # 자료 표시
        text = re.sub(r'<자료\s*(\d+)>', r'\n#### <자료 \1>\n', text)
        
        # 답안양식
        text = re.sub(r'\(답안양식\)', r'\n**[답안양식]**\n', text)
        
        return text
    
    def convert_single_pdf(self, pdf_path, output_path):
        """단일 PDF 파일 변환"""
        print(f"변환 중: {pdf_path.name}")
        
        # 초기화
        self.content = []
        self.table_counter = 0
        
        # 메타데이터
        year = pdf_path.name.split('_')[0]
        self.content.append(f"# {year}년 2차 원가회계 기출문제\n")
        self.content.append(f"> 원본 파일: {pdf_path.name}\n")
        
        # PDF 처리
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                self.content.append(f"\n---\n\n## 페이지 {page_num}\n")
                
                # 구조화된 추출
                text, tables = self.extract_text_with_structure(page)
                
                if text:
                    # 텍스트 처리
                    processed_text = self.process_text(text)
                    
                    # 표가 있는 경우, 텍스트에서 표 영역 제거 시도
                    if tables:
                        # 간단한 휴리스틱: 연속된 숫자나 특수문자가 많은 라인은 표일 가능성
                        lines = processed_text.split('\n')
                        filtered_lines = []
                        table_idx = 0
                        
                        i = 0
                        while i < len(lines):
                            line = lines[i]
                            
                            # 답안양식 발견 시 다음에 표 삽입
                            if '[답안양식]' in line:
                                filtered_lines.append(line)
                                if table_idx < len(tables):
                                    filtered_lines.append("")
                                    filtered_lines.append(self.convert_table_to_markdown(tables[table_idx]))
                                    filtered_lines.append("")
                                    table_idx += 1
                                    # 답안양식 다음 몇 줄은 표 데이터일 가능성이 높으므로 건너뛰기
                                    skip_lines = 5
                                    while skip_lines > 0 and i + 1 < len(lines):
                                        i += 1
                                        skip_lines -= 1
                            else:
                                # 표 데이터로 보이는 라인 필터링
                                if not self.looks_like_table_data(line):
                                    filtered_lines.append(line)
                            
                            i += 1
                        
                        # 처리되지 않은 표 추가
                        while table_idx < len(tables):
                            filtered_lines.append("")
                            filtered_lines.append(self.convert_table_to_markdown(tables[table_idx]))
                            filtered_lines.append("")
                            table_idx += 1
                        
                        self.content.extend(filtered_lines)
                    else:
                        self.content.append(processed_text)
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.content))
        
        print(f"  ✓ 완료: {output_path.name}")
        return True
    
    def looks_like_table_data(self, line):
        """라인이 표 데이터처럼 보이는지 확인"""
        # 짧은 라인은 표가 아닐 가능성이 높음
        if len(line) < 10:
            return False
        
        # 특정 패턴 확인
        table_patterns = [
            r'^\s*[\d,￦]+\s*[\d,￦]+',  # 숫자들
            r'^\s*[XYZ]\s+\d',  # X Y Z 같은 패턴
            r'^\s*#\d+\s+\d',  # #104 같은 패턴
            r'^\s*\d+\s*\|\s*\d+',  # 파이프로 구분된 숫자
        ]
        
        for pattern in table_patterns:
            if re.match(pattern, line):
                return True
        
        return False

def main():
    converter = ImprovedPDFConverter()
    
    # 테스트: 2024년 파일 재변환
    source_file = Path("source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    output_dir = Path("output/markdown_improved")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{source_file.stem}_improved.md"
    
    if source_file.exists():
        converter.convert_single_pdf(source_file, output_file)
        
        # 결과 미리보기
        with open(output_file, 'r', encoding='utf-8') as f:
            preview = f.read()[:2000]
            print("\n--- 개선된 변환 결과 미리보기 ---")
            print(preview)
            print("...")
    else:
        print(f"파일을 찾을 수 없습니다: {source_file}")

if __name__ == "__main__":
    main()
"""
기능: PDF 문서 구조 계층적 분석
입력: PDF 파일
출력: 문서 구조 트리 및 테이블 매핑
"""

import pdfplumber
from pathlib import Path
import re
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class DocumentElement:
    """문서 요소 클래스"""
    type: str  # 'problem', 'sub_question', 'data', 'note', 'table'
    level: int
    page: int
    content: str
    tables: List[int] = None  # 이 요소에 속한 테이블 인덱스
    bbox: tuple = None  # 바운딩 박스 (x0, y0, x1, y1)
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = []

class StructureAnalyzer:
    def __init__(self):
        self.structure = []
        self.tables = []
        self.current_page = 0
        
    def extract_structure(self, pdf_path):
        """PDF에서 구조 추출"""
        print(f"구조 분석 중: {pdf_path.name}")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                self.current_page = page_num
                print(f"\n페이지 {page_num} 분석 중...")
                
                # 페이지 텍스트와 위치 정보 추출
                words = page.extract_words(keep_blank_chars=True)
                
                # 테이블 추출 및 저장
                page_tables = page.extract_tables()
                for table in page_tables:
                    if self._is_valid_table(table):
                        self.tables.append({
                            'page': page_num,
                            'table_index': len(self.tables),
                            'rows': len(table),
                            'cols': len(table[0]) if table else 0,
                            'content': table
                        })
                
                # 텍스트 라인별로 그룹화
                lines = self._group_words_into_lines(words)
                
                # 구조 요소 추출
                for line in lines:
                    self._analyze_line(line, page_num)
        
        return self._build_hierarchy()
    
    def _group_words_into_lines(self, words):
        """단어들을 라인별로 그룹화"""
        if not words:
            return []
        
        # y 좌표로 정렬
        words.sort(key=lambda w: (w['top'], w['x0']))
        
        lines = []
        current_line = [words[0]]
        
        for word in words[1:]:
            # 같은 라인인지 확인 (y 좌표 차이가 작으면)
            if abs(word['top'] - current_line[-1]['top']) < 5:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _analyze_line(self, line_words, page_num):
        """라인 분석하여 구조 요소 추출"""
        # 라인 텍스트 생성
        line_text = ' '.join([w['text'] for w in line_words])
        
        # 바운딩 박스 계산
        x0 = min(w['x0'] for w in line_words)
        y0 = min(w['top'] for w in line_words)
        x1 = max(w['x1'] for w in line_words)
        y1 = max(w['bottom'] for w in line_words)
        bbox = (x0, y0, x1, y1)
        
        # 패턴 매칭
        patterns = {
            'problem': (r'【문제\s*(\d+)】\s*\((\d+)점\)', 1),
            'sub_question': (r'\(물음\s*(\d+)\)', 2),
            'data': (r'<자료\s*(\d+)>', 3),
            'note': (r'※', 4),
            'answer_format': (r'\(답안양식\)', 4),
        }
        
        for elem_type, (pattern, level) in patterns.items():
            match = re.search(pattern, line_text)
            if match:
                element = DocumentElement(
                    type=elem_type,
                    level=level,
                    page=page_num,
                    content=line_text.strip(),
                    bbox=bbox
                )
                self.structure.append(element)
                print(f"  - {elem_type}: {line_text[:50]}...")
                return
    
    def _is_valid_table(self, table):
        """유효한 테이블인지 확인"""
        if not table or len(table) < 2:
            return False
        non_empty = sum(1 for row in table for cell in row if cell and str(cell).strip())
        return non_empty >= 2
    
    def _build_hierarchy(self):
        """평면 구조를 계층 구조로 변환"""
        hierarchy = {
            'title': '2024년 2차 원가회계',
            'pages': {}
        }
        
        current_problem = None
        current_sub_question = None
        
        for elem in self.structure:
            page_key = f'page_{elem.page}'
            if page_key not in hierarchy['pages']:
                hierarchy['pages'][page_key] = {
                    'page_number': elem.page,
                    'problems': []
                }
            
            if elem.type == 'problem':
                current_problem = {
                    'type': 'problem',
                    'content': elem.content,
                    'sub_elements': [],
                    'tables': []
                }
                hierarchy['pages'][page_key]['problems'].append(current_problem)
                current_sub_question = None
                
            elif elem.type == 'sub_question' and current_problem:
                current_sub_question = {
                    'type': 'sub_question',
                    'content': elem.content,
                    'elements': [],
                    'tables': []
                }
                current_problem['sub_elements'].append(current_sub_question)
                
            elif elem.type in ['data', 'note', 'answer_format']:
                target = current_sub_question if current_sub_question else current_problem
                if target:
                    if 'elements' not in target:
                        target['elements'] = []
                    target['elements'].append({
                        'type': elem.type,
                        'content': elem.content
                    })
        
        # 테이블 매핑
        self._map_tables_to_structure(hierarchy)
        
        return hierarchy
    
    def _map_tables_to_structure(self, hierarchy):
        """테이블을 해당하는 구조 요소에 매핑"""
        for table_info in self.tables:
            page_key = f'page_{table_info["page"]}'
            if page_key in hierarchy['pages']:
                page = hierarchy['pages'][page_key]
                # 간단한 휴리스틱: 마지막 문제/물음에 할당
                if page['problems']:
                    last_problem = page['problems'][-1]
                    if last_problem['sub_elements']:
                        last_problem['sub_elements'][-1]['tables'].append(table_info['table_index'])
                    else:
                        last_problem['tables'].append(table_info['table_index'])

def main():
    # 2024년 파일 분석
    pdf_path = Path("source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    
    if not pdf_path.exists():
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    analyzer = StructureAnalyzer()
    structure = analyzer.extract_structure(pdf_path)
    
    # 결과 저장
    output_file = "output-11-document-structure.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    
    # 구조 요약 출력
    print("\n=== 문서 구조 요약 ===")
    for page_key, page_data in structure['pages'].items():
        print(f"\n{page_key} (페이지 {page_data['page_number']})")
        for problem in page_data['problems']:
            print(f"  - {problem['content']}")
            for sub in problem['sub_elements']:
                print(f"    - {sub['content']}")
                if sub['tables']:
                    print(f"      테이블: {len(sub['tables'])}개")
    
    print(f"\n전체 테이블 수: {len(analyzer.tables)}개")
    print(f"구조 분석 완료: {output_file}")

if __name__ == "__main__":
    main()
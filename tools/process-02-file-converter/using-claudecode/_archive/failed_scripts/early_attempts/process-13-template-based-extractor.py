"""
기능: 템플릿 기반 PDF 추출기
입력: PDF 파일 + 구조 템플릿
출력: 구조화된 Markdown
"""

import pdfplumber
from pathlib import Path
import json
import re
from typing import Dict, List, Tuple

class TemplateBasedExtractor:
    def __init__(self, template_path):
        """템플릿 로드"""
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = json.load(f)
        self.current_page = 0
        self.extracted_content = {}
        
    def extract_with_template(self, pdf_path):
        """템플릿 기반 추출"""
        print(f"템플릿 기반 추출 시작: {pdf_path.name}")
        
        with pdfplumber.open(pdf_path) as pdf:
            # 각 페이지별로 템플릿과 매칭
            for page_template in self.template['structure']:
                page_num = page_template['page']
                
                if page_num <= len(pdf.pages):
                    print(f"\n페이지 {page_num} 처리 중...")
                    page = pdf.pages[page_num - 1]
                    
                    # 페이지 내용 추출
                    page_content = self._extract_page_content(page, page_template)
                    self.extracted_content[f'page_{page_num}'] = page_content
        
        return self.extracted_content
    
    def _extract_page_content(self, page, page_template):
        """페이지별 내용 추출"""
        result = {
            'page_number': page_template['page'],
            'page_header': page_template['page_header'],
            'elements': []
        }
        
        # 텍스트와 위치 정보 추출
        words = page.extract_words(keep_blank_chars=True)
        text_blocks = self._group_text_blocks(words)
        
        # 테이블 추출
        tables = page.extract_tables()
        
        # 템플릿 요소별로 매칭
        for element in page_template['elements']:
            extracted = self._match_element(element, text_blocks, tables)
            if extracted:
                result['elements'].append(extracted)
        
        return result
    
    def _group_text_blocks(self, words):
        """텍스트를 의미있는 블록으로 그룹화"""
        if not words:
            return []
        
        # Y 좌표와 X 좌표로 정렬
        words.sort(key=lambda w: (w['top'], w['x0']))
        
        blocks = []
        current_block = {'words': [words[0]], 'bbox': self._get_bbox([words[0]])}
        
        for word in words[1:]:
            # 같은 라인 또는 가까운 위치인지 확인
            if self._is_same_block(current_block['bbox'], word):
                current_block['words'].append(word)
                current_block['bbox'] = self._get_bbox(current_block['words'])
            else:
                current_block['text'] = ' '.join(w['text'] for w in current_block['words'])
                blocks.append(current_block)
                current_block = {'words': [word], 'bbox': self._get_bbox([word])}
        
        # 마지막 블록 추가
        if current_block['words']:
            current_block['text'] = ' '.join(w['text'] for w in current_block['words'])
            blocks.append(current_block)
        
        return blocks
    
    def _is_same_block(self, bbox, word):
        """같은 텍스트 블록인지 확인"""
        # 수직 거리가 가깝고, 수평적으로 연결되어 있으면 같은 블록
        vertical_threshold = 10
        horizontal_threshold = 50
        
        return (abs(word['top'] - bbox[1]) < vertical_threshold or
                (bbox[0] <= word['x0'] <= bbox[2] + horizontal_threshold))
    
    def _get_bbox(self, words):
        """단어들의 바운딩 박스 계산"""
        if not words:
            return (0, 0, 0, 0)
        
        x0 = min(w['x0'] for w in words)
        y0 = min(w['top'] for w in words)
        x1 = max(w['x1'] for w in words)
        y1 = max(w['bottom'] for w in words)
        
        return (x0, y0, x1, y1)
    
    def _match_element(self, element_template, text_blocks, tables):
        """템플릿 요소와 실제 내용 매칭"""
        element_type = element_template['type']
        
        if element_type == 'problem':
            return self._match_problem(element_template, text_blocks, tables)
        elif element_type == 'continuation':
            return self._match_continuation(element_template, text_blocks, tables)
        
        return None
    
    def _match_problem(self, template, text_blocks, tables):
        """문제 매칭"""
        problem_pattern = r'【문제\s*(\d+)】\s*\((\d+)점\)'
        
        for block in text_blocks:
            match = re.search(problem_pattern, block['text'])
            if match and int(match.group(1)) == template['number']:
                print(f"  매칭: {template['content']}")
                
                result = {
                    'type': 'problem',
                    'number': template['number'],
                    'points': template['points'],
                    'content': block['text'],
                    'children': []
                }
                
                # 하위 요소들 처리
                if 'children' in template:
                    for child_template in template['children']:
                        child_result = self._match_child_element(
                            child_template, text_blocks, tables, block['bbox']
                        )
                        if child_result:
                            result['children'].append(child_result)
                
                return result
        
        return None
    
    def _match_child_element(self, template, text_blocks, tables, parent_bbox):
        """하위 요소 매칭"""
        element_type = template['type']
        
        if element_type == 'instruction':
            # ※로 시작하는 지시문 찾기
            for block in text_blocks:
                if '※' in block['text'] and block['bbox'][1] > parent_bbox[1]:
                    return {
                        'type': 'instruction',
                        'content': block['text'],
                        'references': template.get('references', [])
                    }
        
        elif element_type == 'sub_question':
            # (물음 N) 패턴 찾기
            pattern = r'\(물음\s*(\d+)\)'
            for block in text_blocks:
                match = re.search(pattern, block['text'])
                if match and int(match.group(1)) == template['number']:
                    return {
                        'type': 'sub_question',
                        'number': template['number'],
                        'content': block['text'],
                        'answer_format': template.get('answer_format')
                    }
        
        elif element_type == 'data':
            # <자료 N> 패턴 찾기
            pattern = r'<자료\s*(\d+)?>'
            for block in text_blocks:
                if re.search(pattern, block['text']):
                    return {
                        'type': 'data',
                        'id': template['id'],
                        'content': block['text'],
                        'has_tables': template.get('has_tables', False)
                    }
        
        return None
    
    def _match_continuation(self, template, text_blocks, tables):
        """연속 페이지 처리"""
        return {
            'type': 'continuation',
            'parent': template['parent'],
            'children': []
        }
    
    def to_markdown(self):
        """추출된 내용을 Markdown으로 변환"""
        lines = []
        lines.append(f"# {self.template['document']}\n")
        
        for page_key in sorted(self.extracted_content.keys()):
            page_data = self.extracted_content[page_key]
            lines.append(f"\n## 페이지 {page_data['page_number']}\n")
            lines.append(f"*{page_data['page_header']}*\n")
            
            for element in page_data['elements']:
                lines.extend(self._element_to_markdown(element))
        
        return '\n'.join(lines)
    
    def _element_to_markdown(self, element, level=0):
        """요소를 Markdown으로 변환"""
        lines = []
        indent = "  " * level
        
        if element['type'] == 'problem':
            lines.append(f"\n### {element['content']}\n")
            for child in element.get('children', []):
                lines.extend(self._element_to_markdown(child, level + 1))
        
        elif element['type'] == 'instruction':
            lines.append(f"{indent}> {element['content']}\n")
        
        elif element['type'] == 'sub_question':
            lines.append(f"\n{indent}#### {element['content']}\n")
            if element.get('answer_format'):
                lines.append(f"{indent}**[답안양식]**\n")
        
        elif element['type'] == 'data':
            lines.append(f"\n{indent}##### {element['content']}\n")
        
        return lines

def main():
    # 템플릿 로드
    template_path = "structure-template-2024.json"
    pdf_path = Path("source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    
    if not template_path or not pdf_path.exists():
        print("템플릿 또는 PDF 파일을 찾을 수 없습니다.")
        return
    
    # 추출기 생성 및 실행
    extractor = TemplateBasedExtractor(template_path)
    extracted = extractor.extract_with_template(pdf_path)
    
    # Markdown으로 변환
    markdown_content = extractor.to_markdown()
    
    # 저장
    output_file = "output-13-template-based.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n추출 완료: {output_file}")
    
    # 미리보기
    print("\n=== 추출 결과 미리보기 ===")
    print(markdown_content[:1000])
    print("...")

if __name__ == "__main__":
    main()
"""
기능: 구조 템플릿 기반 내용 추출기
입력: 구조 템플릿 파일(.md), 변환된 마크다운 파일(.md)
출력: 구조화된 완성 문서(.md)
"""

import re
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

@dataclass
class StructureElement:
    """구조 요소를 표현하는 클래스"""
    level: int  # 헤딩 레벨 (1-6)
    title: str  # 제목
    content: str  # 내용
    element_type: str  # 'heading', 'table', 'textbox', 'question'
    children: List['StructureElement'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

class StructureBasedExtractor:
    def __init__(self, template_path: str, source_path: str):
        self.template_path = template_path
        self.source_path = source_path
        self.template_structure = None
        self.source_content = None
        
    def load_files(self):
        """템플릿과 소스 파일 로드"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
        
        with open(self.source_path, 'r', encoding='utf-8') as f:
            self.source_content = f.read()
    
    def parse_template_structure(self) -> StructureElement:
        """템플릿의 계층 구조 파싱"""
        root = StructureElement(0, "ROOT", "", "root")
        current_stack = [root]
        
        lines = self.template_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 헤딩 처리
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                
                # 스택 조정
                while len(current_stack) > level:
                    current_stack.pop()
                
                element = StructureElement(level, title, "", "heading")
                current_stack[-1].children.append(element)
                current_stack.append(element)
            
            # 글상자 처리
            elif line.startswith('> 📦'):
                textbox_content = []
                while i < len(lines) and lines[i].startswith('>'):
                    textbox_content.append(lines[i][2:].strip())
                    i += 1
                i -= 1  # 마지막 증가 보정
                
                element = StructureElement(
                    len(current_stack), 
                    "글상자",
                    '\n'.join(textbox_content),
                    "textbox"
                )
                current_stack[-1].children.append(element)
            
            # 표 주석 처리
            elif line.strip().startswith('<!--') and '표' in line:
                element = StructureElement(
                    len(current_stack),
                    line.strip(),
                    "",
                    "table"
                )
                current_stack[-1].children.append(element)
            
            i += 1
        
        return root
    
    def extract_content_for_structure(self, structure: StructureElement, source_text: str) -> str:
        """구조에 맞는 내용 추출"""
        if structure.element_type == "heading":
            # 헤딩 패턴 생성 (문제 번호, 물음 번호 등 고려)
            title_pattern = self._create_flexible_pattern(structure.title)
            
            # 소스에서 매칭되는 섹션 찾기
            pattern = rf'#{{{structure.level}}}\s+{title_pattern}'
            matches = list(re.finditer(pattern, source_text, re.IGNORECASE))
            
            if matches:
                start = matches[0].start()
                # 다음 같은 레벨 헤딩까지의 내용 추출
                next_pattern = rf'#{{{1,{structure.level}}}}\s+'
                next_matches = list(re.finditer(next_pattern, source_text[start+1:]))
                
                if next_matches:
                    end = start + 1 + next_matches[0].start()
                else:
                    end = len(source_text)
                
                return source_text[start:end].strip()
        
        elif structure.element_type == "table":
            # 표 추출 로직
            return self._extract_table(structure.title, source_text)
        
        elif structure.element_type == "textbox":
            # 글상자 내용 추출
            return self._extract_textbox(structure.title, source_text)
        
        return ""
    
    def _create_flexible_pattern(self, title: str) -> str:
        """유연한 패턴 생성 (괄호, 공백 등 고려)"""
        # 특수 문자 이스케이프
        title = re.escape(title)
        
        # 공백을 유연하게 매칭
        title = title.replace(r'\ ', r'\s+')
        
        # 괄호 내용을 옵션으로
        title = re.sub(r'\\\[.*?\\\]', r'.*?', title)
        
        # 숫자 패턴 유연하게
        title = re.sub(r'\\d+', r'\\d+', title)
        
        return title
    
    def _extract_table(self, table_comment: str, source_text: str) -> str:
        """표 추출 (주석 다음의 표 찾기)"""
        # 마크다운 표 패턴
        table_pattern = r'\|[^\n]+\|(?:\n\|[-:\s|]+\|)?(?:\n\|[^\n]+\|)+'
        
        tables = list(re.finditer(table_pattern, source_text, re.MULTILINE))
        
        if tables:
            # 가장 가까운 표 반환 (향후 개선 필요)
            return tables[0].group(0)
        
        return "<!-- 표를 찾을 수 없음 -->"
    
    def _extract_textbox(self, title: str, source_text: str) -> str:
        """글상자 내용 추출"""
        # 글상자 패턴 찾기
        textbox_pattern = r'<자료[^>]*>.*?(?=<자료|$)'
        
        matches = list(re.finditer(textbox_pattern, source_text, re.DOTALL))
        
        if matches:
            return matches[0].group(0)
        
        return "<!-- 글상자 내용을 찾을 수 없음 -->"
    
    def fill_template(self, structure: StructureElement, source_text: str, level: int = 0) -> str:
        """템플릿에 내용 채우기"""
        result = []
        
        if structure.element_type == "heading" and structure.level > 0:
            # 소스에서 내용 추출
            content = self.extract_content_for_structure(structure, source_text)
            if content:
                result.append(content)
            else:
                # 템플릿 헤딩 유지
                result.append(f"{'#' * structure.level} {structure.title}")
        
        # 자식 요소 처리
        for child in structure.children:
            child_result = self.fill_template(child, source_text, level + 1)
            if child_result:
                result.append(child_result)
        
        return '\n\n'.join(result)
    
    def extract(self) -> str:
        """전체 추출 프로세스 실행"""
        self.load_files()
        
        # 템플릿 구조 파싱
        template_structure = self.parse_template_structure()
        
        # 내용 채우기
        filled_content = self.fill_template(template_structure, self.source_content)
        
        return filled_content

def main():
    # 테스트: 2024년 문제 1 추출
    template_path = "structure-templates/2024_2차_원가회계_구조.md"
    source_path = "output-14-layout-aware.md"
    output_path = "output/structured/2024_2차_원가회계_문제1_완성.md"
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 추출기 생성 및 실행
    extractor = StructureBasedExtractor(template_path, source_path)
    result = extractor.extract()
    
    # 결과 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"구조 기반 추출 완료: {output_path}")
    
    # 통계 출력
    print(f"\n추출 통계:")
    print(f"- 템플릿 파일: {template_path}")
    print(f"- 소스 파일: {source_path}")
    print(f"- 결과 크기: {len(result)} 문자")

if __name__ == "__main__":
    main()
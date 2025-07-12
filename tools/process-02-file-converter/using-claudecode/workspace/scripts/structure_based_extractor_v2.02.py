"""
기능: 구조 템플릿 기반 내용 추출기
입력: PDF 파일 + 구조 템플릿
출력: 구조화된 Markdown
"""

import pdfplumber
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional
import json

class StructureBasedExtractor:
    def __init__(self, structure_template_path: Path):
        """
        구조 기반 추출기 초기화
        
        Args:
            structure_template_path: 구조 템플릿 파일 경로
        """
        self.structure = self._load_structure_template(structure_template_path)
        self.content_map = {}
        
    def _load_structure_template(self, template_path: Path) -> Dict:
        """구조 템플릿 로드"""
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        structure = {
            "problems": {},
            "hierarchy": []
        }
        
        with open(template_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_problem = None
        current_subproblem = None
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 메인 문제
            if line.startswith("### 【문제"):
                match = re.match(r"### 【문제\s*(\d+)】\s*\((\d+)점\)\s*(.*)", line)
                if match:
                    problem_num = match.group(1)
                    points = match.group(2)
                    title = match.group(3)
                    
                    current_problem = f"문제{problem_num}"
                    structure["problems"][current_problem] = {
                        "number": problem_num,
                        "points": points,
                        "title": title,
                        "subproblems": {},
                        "sections": {}
                    }
                    structure["hierarchy"].append(current_problem)
            
            # 서브 문제
            elif line.startswith("#### (물음"):
                match = re.match(r"#### \(물음\s*(\d+)\)\s*(.*)", line)
                if match and current_problem:
                    sub_num = match.group(1)
                    sub_desc = match.group(2)
                    
                    current_subproblem = f"물음{sub_num}"
                    structure["problems"][current_problem]["subproblems"][current_subproblem] = {
                        "number": sub_num,
                        "description": sub_desc,
                        "content": []
                    }
            
            # 자료 섹션
            elif line.startswith("##### <자료"):
                match = re.match(r"##### <자료\s*(\d+)>(.*)", line)
                if match and current_problem:
                    data_num = match.group(1)
                    data_title = match.group(2)
                    
                    current_section = f"자료{data_num}"
                    structure["problems"][current_problem]["sections"][current_section] = {
                        "type": "data",
                        "number": data_num,
                        "title": data_title,
                        "content": []
                    }
        
        return structure
    
    def extract_with_structure(self, pdf_path: Path, output_path: Path):
        """
        구조 템플릿을 사용하여 PDF 내용 추출
        
        Args:
            pdf_path: 입력 PDF 경로
            output_path: 출력 Markdown 경로
        """
        print(f"구조 기반 추출 시작: {pdf_path.name}")
        
        # 1. PDF에서 모든 텍스트 추출
        all_text_blocks = self._extract_all_text_blocks(pdf_path)
        
        # 2. 구조와 매칭
        self._match_content_to_structure(all_text_blocks)
        
        # 3. Markdown 생성
        markdown = self._generate_structured_markdown()
        
        # 4. 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"추출 완료: {output_path}")
    
    def _extract_all_text_blocks(self, pdf_path: Path) -> List[Dict]:
        """PDF에서 모든 텍스트 블록 추출"""
        blocks = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 단어 추출
                words = page.extract_words(keep_blank_chars=True)
                
                # 라인으로 그룹화
                lines = self._group_words_into_lines(words)
                
                for line in lines:
                    if line:
                        text = ' '.join(w['text'] for w in line)
                        blocks.append({
                            'text': text.strip(),
                            'page': page_num,
                            'bbox': self._get_bbox_from_words(line),
                            'matched': False
                        })
        
        return blocks
    
    def _group_words_into_lines(self, words):
        """단어를 라인으로 그룹화"""
        if not words:
            return []
        
        words.sort(key=lambda w: (w['top'], w['x0']))
        
        lines = []
        current_line = [words[0]]
        
        for word in words[1:]:
            if abs(word['top'] - current_line[-1]['top']) < 5:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_bbox_from_words(self, words):
        """단어들로부터 바운딩 박스 계산"""
        x0 = min(w['x0'] for w in words)
        y0 = min(w['top'] for w in words)
        x1 = max(w['x1'] for w in words)
        y1 = max(w['bottom'] for w in words)
        return (x0, y0, x1, y1)
    
    def _match_content_to_structure(self, blocks: List[Dict]):
        """텍스트 블록을 구조와 매칭"""
        current_problem = None
        current_subproblem = None
        current_section = None
        
        for block in blocks:
            text = block['text']
            
            # 메인 문제 매칭
            problem_match = re.match(r"【문제\s*(\d+)】", text)
            if problem_match:
                problem_num = problem_match.group(1)
                current_problem = f"문제{problem_num}"
                current_subproblem = None
                current_section = None
                block['matched'] = True
                continue
            
            # 서브 문제 매칭
            sub_match = re.match(r"\(물음\s*(\d+)\)", text)
            if sub_match and current_problem:
                sub_num = sub_match.group(1)
                current_subproblem = f"물음{sub_num}"
                current_section = None
                block['matched'] = True
                continue
            
            # 자료 섹션 매칭
            data_match = re.match(r"<자료\s*(\d+)>", text)
            if data_match and current_problem:
                data_num = data_match.group(1)
                current_section = f"자료{data_num}"
                block['matched'] = True
                continue
            
            # 내용 추가
            if current_problem:
                if current_problem not in self.content_map:
                    self.content_map[current_problem] = {
                        'title_block': None,
                        'content': [],
                        'subproblems': {},
                        'sections': {}
                    }
                
                if current_subproblem:
                    if current_subproblem not in self.content_map[current_problem]['subproblems']:
                        self.content_map[current_problem]['subproblems'][current_subproblem] = []
                    self.content_map[current_problem]['subproblems'][current_subproblem].append(text)
                elif current_section:
                    if current_section not in self.content_map[current_problem]['sections']:
                        self.content_map[current_problem]['sections'][current_section] = []
                    self.content_map[current_problem]['sections'][current_section].append(text)
                else:
                    self.content_map[current_problem]['content'].append(text)
    
    def _generate_structured_markdown(self) -> str:
        """구조화된 Markdown 생성"""
        lines = ["# 2024년 2차 원가회계 기출문제"]
        lines.append("> 구조 템플릿 기반 추출\n")
        
        for problem_key in self.structure['hierarchy']:
            if problem_key in self.structure['problems']:
                problem = self.structure['problems'][problem_key]
                
                # 문제 제목
                lines.append(f"\n### 【문제 {problem['number']}】 ({problem['points']}점) {problem['title']}\n")
                
                # 문제 내용
                if problem_key in self.content_map:
                    content = self.content_map[problem_key]
                    
                    # 메인 내용
                    for text in content.get('content', []):
                        lines.append(f"{text}\n")
                    
                    # 자료 섹션
                    for section_key, section_info in problem.get('sections', {}).items():
                        if section_key in content.get('sections', {}):
                            lines.append(f"\n##### <자료 {section_info['number']}>{section_info.get('title', '')}\n")
                            for text in content['sections'][section_key]:
                                lines.append(f"{text}\n")
                    
                    # 서브 문제
                    for sub_key, sub_info in problem.get('subproblems', {}).items():
                        if sub_key in content.get('subproblems', {}):
                            lines.append(f"\n#### (물음 {sub_info['number']}) {sub_info.get('description', '')}\n")
                            for text in content['subproblems'][sub_key]:
                                lines.append(f"{text}\n")
        
        return '\n'.join(lines)


def main():
    """구조 기반 추출 실행"""
    # Get the script's directory and construct relative paths
    script_dir = Path(__file__).parent.parent  # Go up to workspace/
    
    # 구조 템플릿 경로
    template_path = script_dir / "2024_원가회계_헤딩_구조.md"
    
    # PDF 경로
    pdf_path = script_dir.parent / "_source" / "2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf"
    
    # 출력 경로
    output_path = script_dir.parent / "output" / "converted_files" / "2024_원가회계_v2.02_structure_based.md"
    
    if template_path.exists() and pdf_path.exists():
        extractor = StructureBasedExtractor(template_path)
        extractor.extract_with_structure(pdf_path, output_path)
        
        # 결과 미리보기
        with open(output_path, 'r', encoding='utf-8') as f:
            preview = f.read()[:2000]
            print("\n=== 추출 결과 미리보기 ===")
            print(preview)
            print("...")
    else:
        if not template_path.exists():
            print(f"❌ 템플릿 파일을 찾을 수 없습니다: {template_path}")
        if not pdf_path.exists():
            print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")


if __name__ == "__main__":
    main()
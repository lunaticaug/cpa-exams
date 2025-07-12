"""
기능: 간단한 구조 기반 내용 채우기
입력: 변환된 마크다운 파일
출력: 문제별로 구조화된 파일
"""

import re
import os
from typing import Dict, List, Optional

class SimpleStructureFiller:
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.source_content = None
        self.problems = {}
        
    def load_source(self):
        """소스 파일 로드"""
        with open(self.source_path, 'r', encoding='utf-8') as f:
            self.source_content = f.read()
    
    def extract_problem(self, problem_num: int) -> Dict[str, any]:
        """특정 문제 추출"""
        # 문제 패턴
        problem_pattern = rf'##\s*【문제\s*{problem_num}】.*?(?=##\s*【문제|$)'
        
        match = re.search(problem_pattern, self.source_content, re.DOTALL)
        if not match:
            return None
        
        problem_content = match.group(0)
        
        # 문제 정보 추출
        result = {
            'number': problem_num,
            'full_content': problem_content,
            'title': self._extract_title(problem_content),
            'points': self._extract_points(problem_content),
            'materials': self._extract_materials(problem_content),
            'questions': self._extract_questions(problem_content),
            'tables': self._extract_tables(problem_content)
        }
        
        return result
    
    def _extract_title(self, content: str) -> str:
        """문제 제목 추출"""
        match = re.search(r'##\s*【문제\s*\d+】\s*\((\d+)점\)', content)
        if match:
            return match.group(0)
        return ""
    
    def _extract_points(self, content: str) -> int:
        """배점 추출"""
        match = re.search(r'\((\d+)점\)', content)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_materials(self, content: str) -> List[Dict]:
        """자료 추출"""
        materials = []
        
        # <자료 N> 패턴
        material_pattern = r'###?\s*<자료\s*(\d+)>.*?(?=###?\s*<자료|###?\s*\(물음|$)'
        
        for match in re.finditer(material_pattern, content, re.DOTALL):
            material_num = int(match.group(1))
            material_content = match.group(0)
            
            materials.append({
                'number': material_num,
                'content': material_content,
                'textbox': self._extract_textbox_content(material_content),
                'tables': self._extract_tables(material_content)
            })
        
        return materials
    
    def _extract_questions(self, content: str) -> List[Dict]:
        """물음 추출"""
        questions = []
        
        # (물음 N) 패턴
        question_pattern = r'####?\s*\(물음\s*(\d+)\).*?(?=####?\s*\(물음|##|$)'
        
        for match in re.finditer(question_pattern, content, re.DOTALL):
            question_num = int(match.group(1))
            question_content = match.group(0)
            
            # 세부 물음 확인
            sub_questions = []
            sub_pattern = r'#####\s*\((\d+)\)'
            for sub_match in re.finditer(sub_pattern, question_content):
                sub_questions.append(int(sub_match.group(1)))
            
            questions.append({
                'number': question_num,
                'content': question_content,
                'sub_questions': sub_questions,
                'answer_format': self._extract_answer_format(question_content)
            })
        
        return questions
    
    def _extract_textbox_content(self, content: str) -> str:
        """글상자 내용 추출"""
        # 들여쓰기된 내용 찾기
        lines = content.split('\n')
        textbox_lines = []
        in_textbox = False
        
        for line in lines:
            if '보조부문 원가를' in line or '개별원가계산' in line:
                in_textbox = True
            elif in_textbox and (line.strip() == '' or not line.startswith(' ')):
                break
            elif in_textbox:
                textbox_lines.append(line.strip())
        
        return '\n'.join(textbox_lines)
    
    def _extract_tables(self, content: str) -> List[str]:
        """표 추출"""
        tables = []
        
        # 마크다운 표 패턴
        table_pattern = r'\|[^\n]+\|(?:\n\|[-:\s|]+\|)?(?:\n\|[^\n]+\|)+'
        
        for match in re.finditer(table_pattern, content, re.MULTILINE):
            tables.append(match.group(0))
        
        return tables
    
    def _extract_answer_format(self, content: str) -> Optional[str]:
        """답안양식 추출"""
        # [답안양식] 다음의 내용 찾기
        match = re.search(r'\[답안양식\](.*?)(?=\n\n|$)', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def create_structured_output(self, problem: Dict) -> str:
        """구조화된 출력 생성"""
        output = []
        
        # 제목
        output.append(f"# 2024년 2차 원가회계 - 문제 {problem['number']}")
        output.append(f"\n{problem['title']}\n")
        
        # 자료
        for material in problem['materials']:
            output.append(f"## 자료 {material['number']}")
            
            if material['textbox']:
                output.append("\n### 📦 글상자 내용")
                output.append(material['textbox'])
            
            if material['tables']:
                output.append("\n### 📊 표 데이터")
                for i, table in enumerate(material['tables'], 1):
                    output.append(f"\n#### 표 {material['number']}-{i}")
                    output.append(table)
        
        # 물음
        output.append("\n## 물음 및 답안")
        for question in problem['questions']:
            output.append(f"\n### (물음 {question['number']})")
            
            # 물음 내용 추출
            lines = question['content'].split('\n')
            question_text = []
            for line in lines[1:]:  # 첫 줄(제목) 제외
                if line.strip() and not line.startswith('#'):
                    question_text.append(line.strip())
                if '[답안양식]' in line:
                    break
            
            if question_text:
                output.append('\n'.join(question_text))
            
            # 세부 물음
            if question['sub_questions']:
                for sub_num in question['sub_questions']:
                    output.append(f"\n#### ({sub_num})")
            
            # 답안양식
            if question['answer_format']:
                output.append("\n**[답안양식]**")
                output.append(question['answer_format'])
        
        # 표 요약
        output.append("\n## 표 요약")
        output.append(f"- 총 {len(problem['tables'])}개의 표")
        output.append(f"- 자료: {len(problem['materials'])}개")
        output.append(f"- 물음: {len(problem['questions'])}개")
        
        return '\n'.join(output)

def main():
    # 소스 파일
    source_path = "output-14-layout-aware.md"
    
    # 추출기 생성
    filler = SimpleStructureFiller(source_path)
    filler.load_source()
    
    # 문제 1 추출
    problem1 = filler.extract_problem(1)
    
    if problem1:
        # 구조화된 출력 생성
        structured_output = filler.create_structured_output(problem1)
        
        # 저장
        output_path = "output/structured/2024_원가회계_문제1_구조화.md"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(structured_output)
        
        print(f"구조화 완료: {output_path}")
        print(f"\n추출 정보:")
        print(f"- 배점: {problem1['points']}점")
        print(f"- 자료 수: {len(problem1['materials'])}개")
        print(f"- 물음 수: {len(problem1['questions'])}개")
        print(f"- 표 수: {len(problem1['tables'])}개")
    else:
        print("문제 1을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
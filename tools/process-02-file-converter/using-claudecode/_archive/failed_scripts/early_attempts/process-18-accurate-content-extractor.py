"""
기능: 정확한 내용 추출기 - 본문, 글상자, 표를 정확히 구분
입력: 변환된 마크다운 파일
출력: 원문에 충실한 구조화 문서
"""

import re
import os
from typing import Dict, List, Tuple, Optional
import json

class AccurateContentExtractor:
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.source_content = ""
        self.pages = []
        
    def load_file(self):
        """파일 로드 및 페이지 분리"""
        with open(self.source_path, 'r', encoding='utf-8') as f:
            self.source_content = f.read()
        
        # 페이지별로 분리
        self.pages = re.split(r'---\n\n## 페이지 \d+', self.source_content)
    
    def extract_problem_structure(self) -> Dict[int, Dict]:
        """문제별 구조 추출"""
        problems = {}
        
        # 문제 패턴
        problem_pattern = r'【문제\s*(\d+)】\s*\((\d+)점\)'
        
        matches = list(re.finditer(problem_pattern, self.source_content))
        
        for i, match in enumerate(matches):
            problem_num = int(match.group(1))
            points = int(match.group(2))
            
            # 문제 시작과 끝
            start = match.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(self.source_content)
            
            problem_content = self.source_content[start:end]
            
            # 문제 구조 분석
            problems[problem_num] = self._analyze_problem_content(
                problem_num, points, problem_content
            )
        
        return problems
    
    def _analyze_problem_content(self, num: int, points: int, content: str) -> Dict:
        """문제 내용 상세 분석"""
        result = {
            'number': num,
            'points': points,
            'title': '',
            'intro_text': '',  # 문제 소개 텍스트
            'materials': [],
            'questions': [],
            'tables': []
        }
        
        # 문제 제목 추출
        title_match = re.search(r'(【문제\s*\d+】\s*\(\d+점\))(.*?)(?=\n)', content)
        if title_match:
            result['title'] = title_match.group(1)
            
        # 문제 소개 텍스트 추출 (자료 전까지)
        intro_pattern = r'【문제\s*\d+】.*?\n\n(.*?)(?=<자료|####?\s*\(물음|$)'
        intro_match = re.search(intro_pattern, content, re.DOTALL)
        if intro_match:
            intro_text = intro_match.group(1).strip()
            # 실제 본문만 추출 (물음 제외)
            intro_lines = []
            for line in intro_text.split('\n'):
                if not re.match(r'^\(물음', line.strip()):
                    intro_lines.append(line)
                else:
                    break
            result['intro_text'] = '\n'.join(intro_lines).strip()
        
        # 자료 추출
        result['materials'] = self._extract_materials(content)
        
        # 물음 추출
        result['questions'] = self._extract_questions(content)
        
        # 표 추출
        result['tables'] = self._extract_tables(content)
        
        return result
    
    def _extract_materials(self, content: str) -> List[Dict]:
        """자료 정확히 추출"""
        materials = []
        
        # <자료 N> 패턴
        material_pattern = r'(<자료\s*(\d+)>.*?)(?=<자료\s*\d+>|####?\s*\(물음|【문제|$)'
        
        for match in re.finditer(material_pattern, content, re.DOTALL):
            material_num = match.group(2) if match.group(2) else '1'
            material_content = match.group(1)
            
            # 글상자 내용 추출 (들여쓰기된 부분)
            textbox_content = self._extract_textbox_content(material_content)
            
            # 자료 내 표 추출
            tables = self._extract_tables(material_content)
            
            materials.append({
                'number': material_num,
                'raw_content': material_content,
                'textbox_content': textbox_content,
                'tables': tables
            })
        
        return materials
    
    def _extract_textbox_content(self, material_content: str) -> str:
        """글상자 내용만 정확히 추출"""
        lines = material_content.split('\n')
        textbox_lines = []
        in_textbox = False
        
        for i, line in enumerate(lines):
            # <자료> 다음 줄부터 시작
            if '<자료' in line:
                in_textbox = True
                continue
            
            # 표가 시작되면 종료
            if in_textbox and '|' in line:
                break
            
            # 물음이 나오면 종료
            if in_textbox and re.match(r'^\(물음', line.strip()):
                break
            
            # 빈 줄이 연속으로 나오면 종료
            if in_textbox and line.strip() == '' and i+1 < len(lines) and lines[i+1].strip() == '':
                break
            
            # 글상자 내용 수집
            if in_textbox and line.strip():
                textbox_lines.append(line.strip())
        
        return '\n'.join(textbox_lines)
    
    def _extract_questions(self, content: str) -> List[Dict]:
        """물음 정확히 추출"""
        questions = []
        
        # (물음 N) 패턴
        question_pattern = r'\(물음\s*(\d+)\)(.*?)(?=\(물음\s*\d+\)|【문제|$)'
        
        for match in re.finditer(question_pattern, content, re.DOTALL):
            q_num = int(match.group(1))
            q_content = match.group(2).strip()
            
            # 물음 텍스트만 추출 (답안양식 전까지)
            q_text = ""
            if '[답안양식]' in q_content:
                q_text = q_content.split('[답안양식]')[0].strip()
            else:
                # 첫 줄만 추출
                q_text = q_content.split('\n')[0].strip()
            
            # 답안양식 추출
            answer_format = ""
            if '[답안양식]' in q_content:
                format_start = q_content.find('[답안양식]')
                # 다음 물음이나 표까지
                format_content = q_content[format_start:]
                answer_format = self._extract_answer_format(format_content)
            
            questions.append({
                'number': q_num,
                'text': q_text,
                'answer_format': answer_format,
                'raw_content': match.group(0)
            })
        
        return questions
    
    def _extract_answer_format(self, content: str) -> str:
        """답안양식 추출"""
        # [답안양식] 다음부터 표 또는 다음 섹션까지
        lines = content.split('\n')
        format_lines = []
        started = False
        
        for line in lines:
            if '[답안양식]' in line:
                started = True
                continue
            
            if started:
                # 표가 있으면 포함
                if '|' in line:
                    format_lines.append(line)
                # 빈 줄 이후 텍스트가 있으면 종료
                elif line.strip() == '':
                    if format_lines:
                        break
                else:
                    format_lines.append(line)
        
        return '\n'.join(format_lines).strip()
    
    def _extract_tables(self, content: str) -> List[Dict]:
        """표 추출"""
        tables = []
        table_pattern = r'(\|[^\n]+\|(?:\n\|[-:\s|]+\|)?(?:\n\|[^\n]+\|)+)'
        
        for i, match in enumerate(re.finditer(table_pattern, content, re.MULTILINE)):
            table_text = match.group(0)
            lines = table_text.strip().split('\n')
            
            # 행과 열 계산
            rows = len([l for l in lines if l.strip() and '---' not in l])
            cols = len(lines[0].split('|')) - 2
            
            tables.append({
                'index': i + 1,
                'content': table_text,
                'rows': rows,
                'cols': cols
            })
        
        return tables
    
    def create_accurate_document(self, problems: Dict[int, Dict]) -> str:
        """원문에 충실한 문서 생성"""
        output = ["# 2024년 2차 원가회계 기출문제\n"]
        
        for prob_num in sorted(problems.keys()):
            prob = problems[prob_num]
            
            # 문제 제목
            output.append(f"## {prob['title']}")
            
            # 문제 소개 텍스트
            if prob['intro_text']:
                output.append(f"\n{prob['intro_text']}\n")
            
            # 자료
            for material in prob['materials']:
                output.append(f"### <자료 {material['number']}>")
                
                # 글상자 내용
                if material['textbox_content']:
                    output.append(material['textbox_content'])
                    output.append("")
                
                # 표
                for table in material['tables']:
                    output.append(table['content'])
                    output.append("")
            
            # 물음
            output.append("### 물음")
            for question in prob['questions']:
                output.append(f"\n#### (물음 {question['number']})")
                output.append(question['text'])
                
                if question['answer_format']:
                    output.append("\n**[답안양식]**")
                    output.append(question['answer_format'])
            
            output.append("\n---\n")
        
        return '\n'.join(output)

def main():
    # 파일 경로
    source_path = "output-14-layout-aware.md"
    output_path = "output/structured/2024_2차_원가회계_정확한_추출.md"
    
    # 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 추출기 실행
    extractor = AccurateContentExtractor(source_path)
    extractor.load_file()
    
    # 문제 구조 추출
    problems = extractor.extract_problem_structure()
    
    # 정확한 문서 생성
    accurate_doc = extractor.create_accurate_document(problems)
    
    # 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(accurate_doc)
    
    print(f"✅ 정확한 추출 완료: {output_path}")
    
    # 통계 출력
    for num, prob in sorted(problems.items()):
        print(f"\n문제 {num} ({prob['points']}점):")
        print(f"- 소개 텍스트: {len(prob['intro_text'])} 문자")
        print(f"- 자료: {len(prob['materials'])}개")
        print(f"- 물음: {len(prob['questions'])}개")
        print(f"- 표: {len(prob['tables'])}개")

if __name__ == "__main__":
    main()
"""
기능: 개선된 구조 기반 내용 추출기
입력: 구조 템플릿과 변환된 마크다운 파일
출력: 완전히 구조화된 문서
"""

import re
import os
from typing import Dict, List, Tuple, Optional
import json

class ImprovedStructureExtractor:
    def __init__(self, template_path: str, source_path: str):
        self.template_path = template_path
        self.source_path = source_path
        self.template_content = ""
        self.source_content = ""
        
    def load_files(self):
        """파일 로드"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
        
        with open(self.source_path, 'r', encoding='utf-8') as f:
            self.source_content = f.read()
    
    def extract_all_problems(self) -> Dict[int, Dict]:
        """모든 문제 추출"""
        problems = {}
        
        # 문제 패턴 찾기 - 더 유연하게
        problem_pattern = r'【문제\s*(\d+)】\s*\((\d+)점\)'
        
        # 모든 문제 위치 찾기
        matches = list(re.finditer(problem_pattern, self.source_content))
        
        for i, match in enumerate(matches):
            problem_num = int(match.group(1))
            points = int(match.group(2))
            
            # 문제의 시작과 끝 찾기
            start = match.start()
            # 다음 문제까지 또는 파일 끝까지
            end = matches[i+1].start() if i+1 < len(matches) else len(self.source_content)
            
            content = self.source_content[start:end]
            
            # 주요 주제 추출
            subject = ""
            
            problems[problem_num] = {
                'number': problem_num,
                'points': points,
                'subject': subject,
                'full_content': content,
                'materials': self._extract_materials(content),
                'questions': self._extract_questions(content),
                'tables': self._extract_all_tables(content)
            }
        
        return problems
    
    def _extract_materials(self, content: str) -> List[Dict]:
        """자료 추출 개선"""
        materials = []
        
        # <자료 N> 패턴
        material_pattern = r'###\s*(<자료\s*(\d+)>.*?)(?=###|####\s*\(물음|##\s*【문제|$)'
        
        for match in re.finditer(material_pattern, content, re.DOTALL):
            material_num = match.group(2) if match.group(2) else str(len(materials) + 1)
            material_content = match.group(1)
            
            # 글상자 내용 추출
            textbox_content = self._extract_textbox_info(material_content)
            
            # 표 추출
            tables = self._extract_tables_in_section(material_content)
            
            materials.append({
                'number': material_num,
                'title': f"자료 {material_num}",
                'content': material_content.strip(),
                'textbox': textbox_content,
                'tables': tables
            })
        
        # 공통자료나 특수 자료 패턴도 확인
        if not materials:
            # "※ <자료" 패턴
            special_pattern = r'※\s*<자료.*?>.*?(?=####\s*\(물음|##\s*【문제|$)'
            for match in re.finditer(special_pattern, content, re.DOTALL):
                materials.append({
                    'number': '공통',
                    'title': '공통자료',
                    'content': match.group(0),
                    'textbox': self._extract_textbox_info(match.group(0)),
                    'tables': self._extract_tables_in_section(match.group(0))
                })
        
        return materials
    
    def _extract_textbox_info(self, content: str) -> Dict:
        """글상자 정보 추출"""
        # 줄 단위로 분석
        lines = content.split('\n')
        textbox_lines = []
        textbox_started = False
        
        for line in lines:
            # 글상자 시작 패턴
            if any(keyword in line for keyword in ['㈜한국', '보조부문', '종합원가', '회계연도', '적용하']):
                textbox_started = True
            
            # 글상자 내용 수집
            if textbox_started:
                if line.strip() and not line.strip().startswith('#'):
                    textbox_lines.append(line.strip())
                # 표나 다른 섹션 시작시 종료
                elif '|' in line or line.strip().startswith('#'):
                    break
        
        return {
            'content': '\n'.join(textbox_lines),
            'type': '설명' if textbox_lines else None
        }
    
    def _extract_questions(self, content: str) -> List[Dict]:
        """물음 추출 개선"""
        questions = []
        
        # (물음 N) 패턴 - 더 유연하게
        question_pattern = r'####\s*\(물음\s*(\d+)\)(.*?)(?=####\s*\(물음|###|##\s*【문제|$)'
        
        for match in re.finditer(question_pattern, content, re.DOTALL):
            q_num = int(match.group(1))
            q_content = match.group(2).strip()
            
            # 물음 텍스트 추출
            q_text_lines = []
            for line in q_content.split('\n'):
                if line.strip() and not line.startswith('#') and '[답안양식]' not in line:
                    q_text_lines.append(line.strip())
                if '[답안양식]' in line:
                    break
            
            # 세부 물음 찾기
            sub_questions = []
            sub_pattern = r'#####\s*\((\d+)\)'
            for sub_match in re.finditer(sub_pattern, q_content):
                sub_questions.append(int(sub_match.group(1)))
            
            # 답안양식 추출
            answer_format = ""
            if '[답안양식]' in q_content:
                format_match = re.search(r'\[답안양식\](.*?)(?=####|###|$)', q_content, re.DOTALL)
                if format_match:
                    answer_format = format_match.group(1).strip()
            
            questions.append({
                'number': q_num,
                'text': ' '.join(q_text_lines),
                'sub_questions': sub_questions,
                'answer_format': answer_format,
                'full_content': match.group(0)
            })
        
        return questions
    
    def _extract_tables_in_section(self, content: str) -> List[Dict]:
        """섹션 내 표 추출"""
        tables = []
        
        # 마크다운 표 패턴
        table_pattern = r'(\|[^\n]+\|(?:\n\|[-:\s|]+\|)?(?:\n\|[^\n]+\|)+)'
        
        for i, match in enumerate(re.finditer(table_pattern, content, re.MULTILINE)):
            table_text = match.group(0)
            
            # 표 분석
            lines = table_text.strip().split('\n')
            if len(lines) >= 2:  # 헤더 + 구분선 이상
                # 행과 열 수 계산
                rows = len([l for l in lines if l.strip() and '---' not in l])
                cols = len(lines[0].split('|')) - 2  # 앞뒤 | 제외
                
                tables.append({
                    'index': i + 1,
                    'content': table_text,
                    'rows': rows,
                    'cols': cols,
                    'description': f"{rows}x{cols} 표"
                })
        
        return tables
    
    def _extract_all_tables(self, content: str) -> List[Dict]:
        """전체 내용에서 모든 표 추출"""
        return self._extract_tables_in_section(content)
    
    def create_structured_document(self, problems: Dict[int, Dict]) -> str:
        """구조화된 문서 생성"""
        output = ["# 2024년 2차 원가회계 기출문제 - 구조화 완성본\n"]
        
        for prob_num in sorted(problems.keys()):
            prob = problems[prob_num]
            
            # 문제 제목
            output.append(f"## 【문제 {prob['number']}】 ({prob['points']}점)")
            if prob['subject']:
                output.append(f"**주요 개념**: {prob['subject']}\n")
            
            # 자료
            for material in prob['materials']:
                output.append(f"### <자료 {material['number']}>")
                
                if material['textbox']['content']:
                    output.append("> 📦 **글상자 내용**")
                    for line in material['textbox']['content'].split('\n'):
                        if line.strip():
                            output.append(f"> {line}")
                    output.append("")
                
                # 표
                for table in material['tables']:
                    output.append(f"#### 표 {material['number']}-{table['index']}: {table['description']}")
                    output.append(table['content'])
                    output.append("")
            
            # 물음
            if prob['questions']:
                output.append("### 물음")
                
                for question in prob['questions']:
                    output.append(f"\n#### (물음 {question['number']})")
                    if question['text']:
                        output.append(question['text'])
                    
                    # 세부 물음
                    for sub_num in question['sub_questions']:
                        output.append(f"\n##### ({sub_num})")
                        output.append("[세부 물음 내용]")
                    
                    # 답안양식
                    if question['answer_format']:
                        output.append("\n**[답안양식]**")
                        output.append(question['answer_format'])
            
            # 구분선
            output.append("\n---\n")
        
        # 요약 통계
        output.append("## 문서 요약 통계\n")
        total_points = sum(p['points'] for p in problems.values())
        total_materials = sum(len(p['materials']) for p in problems.values())
        total_questions = sum(len(p['questions']) for p in problems.values())
        total_tables = sum(len(p['tables']) for p in problems.values())
        
        output.append(f"- 총 문제 수: {len(problems)}개")
        output.append(f"- 총 배점: {total_points}점")
        output.append(f"- 총 자료 수: {total_materials}개")
        output.append(f"- 총 물음 수: {total_questions}개")
        output.append(f"- 총 표 수: {total_tables}개")
        
        return '\n'.join(output)

def main():
    # 파일 경로
    template_path = "structure-templates/2024_2차_원가회계_구조.md"
    source_path = "output-14-layout-aware.md"
    output_path = "output/structured/2024_2차_원가회계_전체_구조화.md"
    
    # 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 추출기 실행
    extractor = ImprovedStructureExtractor(template_path, source_path)
    extractor.load_files()
    
    # 모든 문제 추출
    problems = extractor.extract_all_problems()
    
    # 구조화된 문서 생성
    structured_doc = extractor.create_structured_document(problems)
    
    # 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(structured_doc)
    
    print(f"✅ 구조화 완료: {output_path}")
    print(f"\n📊 추출 통계:")
    for num, prob in sorted(problems.items()):
        print(f"- 문제 {num}: {prob['points']}점, "
              f"자료 {len(prob['materials'])}개, "
              f"물음 {len(prob['questions'])}개, "
              f"표 {len(prob['tables'])}개")
    
    # JSON으로도 저장
    json_path = output_path.replace('.md', '.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON 저장: {json_path}")

if __name__ == "__main__":
    main()